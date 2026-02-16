import os
import io
import csv
import time
import random
import logging
import threading
import queue
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

from .normalizer import UniversalNormalizer

load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s')
logger = logging.getLogger("GDriveETLv4")

# Configuration Constants
ROOT_FOLDER_ID = "1ltTYjekxZsk2CdF20tSk1B2FnRn4119E"
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), 'honey-bee-digital-d96daf6e6faf.json')
# DB Config
DB_USER = os.getenv('DB_USER')
DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT', '3306')
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

class GDriveHighSpeedIngestor:
    def __init__(self):
        self.creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive.readonly'])
        self.engine = create_engine(DATABASE_URI, pool_size=35, max_overflow=25, pool_pre_ping=True, pool_recycle=3600, isolation_level="READ COMMITTED")
        self.table_name = "raw_google_map_drive_data"
        self.task_queue = queue.Queue(maxsize=100)
        self.folder_registry = set()
        self.shutdown_event = threading.Event()
        self.scanners_finished = threading.Event()
        self._tls = threading.local()
        self.first_run = True # Track if we need an initial full scan

    def get_service(self):
        if not hasattr(self._tls, 'service'):
            self._tls.service = build('drive', 'v3', credentials=self.creds)
        return self._tls.service

    def retry_on_429(func):
        def wrapper(*args, **kwargs):
            for attempt in range(5):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if '429' in str(e) or 'rate limit' in str(e).lower():
                        wait = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited. Retrying in {wait:.2f}s...")
                        time.sleep(wait)
                    else: raise
            return func(*args, **kwargs)
        return wrapper

    def load_registry(self):
        """Load already processed file IDs, folder timestamps, and change token."""
        with self.engine.connect() as conn:
            # Load processed files
            query_str = f"SELECT DISTINCT drive_file_id FROM {self.table_name}"
            res = conn.exec_driver_sql(query_str)
            self.processed_files = {r[0] for r in res if r[0]}
            
            # Load processed folders with timestamps
            rows = conn.exec_driver_sql("SELECT folder_id, drive_modified_at FROM drive_folder_registry").fetchall()
            self.folder_registry = {r[0]: r[1] for r in rows}

            # Load Last Change Token
            meta = conn.exec_driver_sql("SELECT meta_value FROM etl_metadata WHERE meta_key = 'last_change_token'").fetchone()
            self.page_token = meta[0] if meta else None

        logger.info(f"📁 Registry loaded: {len(self.processed_files)} files, {len(self.folder_registry)} folders.")

    def save_change_token(self, token):
        with self.engine.begin() as conn:
            conn.execute(text("INSERT INTO etl_metadata (meta_key, meta_value) VALUES ('last_change_token', :token) ON DUPLICATE KEY UPDATE meta_value = :token"), {"token": token})

    def get_changes(self):
        """Fetch all pending changes from Google Drive since last token."""
        service = self.get_service()
        if not self.page_token:
            token_res = service.changes().getStartPageToken().execute()
            self.page_token = token_res.get('startPageToken')
            self.save_change_token(self.page_token)
            return []

        try:
            all_changes = []
            current_token = self.page_token
            while True:
                response = service.changes().list(
                    pageToken=current_token, 
                    spaces='drive', 
                    pageSize=100,
                    fields="nextPageToken, newStartPageToken, changes(fileId, removed, file(id, name, mimeType, parents, modifiedTime))"
                ).execute()
                all_changes.extend(response.get('changes', []))
                if 'nextPageToken' in response:
                    current_token = response['nextPageToken']
                else:
                    self.page_token = response.get('newStartPageToken') or current_token
                    break
            
            return all_changes
        except Exception as e:
            logger.warning(f"Changes API error: {e}. Token might be expired.")
            token_res = service.changes().getStartPageToken().execute()
            self.page_token = token_res.get('startPageToken')
            self.save_change_token(self.page_token)
            return []

    def register_folder(self, folder_id, folder_name, modified_at, csv_count=0):
        with self.engine.begin() as conn:
            sql = text("""
                INSERT INTO drive_folder_registry (folder_id, folder_name, drive_modified_at, csv_count, status, scanned_at) 
                VALUES (:id, :name, :mod, :count, 'Updated', NOW()) 
                ON DUPLICATE KEY UPDATE 
                    drive_modified_at=:mod, 
                    csv_count=:count, 
                    status='Updated',
                    scanned_at=NOW()
            """)
            conn.execute(sql, {"id": folder_id, "name": folder_name, "mod": modified_at, "count": csv_count})
            self.folder_registry[folder_id] = modified_at

    @retry_on_429
    def list_files(self, parent_id):
        return self.get_service().files().list(
            q=f"'{parent_id}' in parents and trashed=false", 
            fields="files(id, name, mimeType, modifiedTime)",
            orderBy="modifiedTime desc"
        ).execute().get('files', [])

    def scanner_producer(self, folder_id, folder_name, path=""):
        if self.shutdown_event.is_set(): return
        
        # 1. Fetch items
        items = self.list_files(folder_id)
        
        # 2. Get folder metadata if needed (or use parent's item info)
        # For simplicity, we assume we want to scan all top folders at least once
        
        logger.info(f"📂 Path: {path}/{folder_name}")
        
        csv_processed = 0
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # Recursive Scan
                # SMART SYNC: Check modification time if we already have it
                last_mod = self.folder_registry.get(item['id'])
                current_mod = item.get('modifiedTime')
                
                if last_mod == current_mod:
                    # Skip sub-folder logic could be here, but GDrive modifiedTime 
                    # doesn't always bubble up perfectly. We'll scan folders
                    # but skip files inside based on file_id.
                    pass 

                self.scanner_producer(item['id'], item['name'], f"{path}/{folder_name}")
            
            elif item['name'].lower().endswith('.csv'):
                # SMART SYNC: Skip if file_id is already in our processed set
                if item['id'] in self.processed_files:
                    logger.info(f"⏭ SKIPPED: {item['name']}")
                    continue
                    
                logger.info(f"🆕 NEW: {item['name']}")
                self.task_queue.put({
                    "file_id": item['id'], "file_name": item['name'],
                    "folder_id": folder_id, "folder_name": folder_name,
                    "path": f"{path}/{folder_name}", "modifiedTime": item.get('modifiedTime')
                })
                csv_processed += 1
        
        # Update folder state
        # We find the modifiedTime for THIS folder from its parent or API
        # but for simplicity we'll just use the latest file's time or NOW
        mod_time = datetime.utcnow().isoformat() + "Z"
        if items:
            mod_time = items[0].get('modifiedTime', mod_time)
            
        self.register_folder(folder_id, folder_name, mod_time, csv_processed)

    @retry_on_429
    def download_csv(self, file_id):
        request = self.get_service().files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done: _, done = downloader.next_chunk()
        fh.seek(0)
        return io.TextIOWrapper(fh, encoding='utf-8', errors='replace')

    def worker_consumer(self):
        while not self.shutdown_event.is_set():
            try:
                task = self.task_queue.get(timeout=5)
                self.process_file(task)
                self.task_queue.task_done()
            except queue.Empty:
                if self.scanners_finished.is_set(): break
                continue

    def process_file(self, task):
        try:
            # logger.info(f"📥 Processing: {task['file_name']}")
            stream = self.download_csv(task['file_id'])
            reader = csv.DictReader(stream)
            batch = []
            row_count = 0
            for row in reader:
                norm_row = UniversalNormalizer.normalize_row({
                    **row, "drive_file_id": task["file_id"], "drive_file_name": task["file_name"],
                    "drive_folder_id": task["folder_id"], "drive_folder_name": task["folder_name"],
                    "drive_file_path": task["path"], "drive_uploaded_time": task["modifiedTime"]
                })
                batch.append(norm_row)
                row_count += 1
                if len(batch) >= 2000: # Increased batch size for speed
                    self.commit_batch(batch)
                    batch = []
            if batch: self.commit_batch(batch)
            logger.info(f"✅ DONE: {task['path']}/{task['file_name']} added successfully ({row_count} rows)")
        except Exception as e:
            logger.error(f"❌ Error processing {task['file_name']}: {e}")

    def commit_batch(self, batch):
        if not batch: return
        sql = text("""
            INSERT IGNORE INTO raw_google_map_drive_data (name, address, website, phone_number, reviews_count, reviews_average, category, subcategory, city, state, area, drive_folder_id, drive_folder_name, drive_file_id, drive_file_name, drive_file_path, drive_uploaded_time)
            VALUES (:name, :address, :website, :phone_number, :reviews_count, :reviews_average, :category, :subcategory, :city, :state, :area, :drive_folder_id, :drive_folder_name, :drive_file_id, :drive_file_name, :drive_file_path, :drive_uploaded_time)
        """)
        # We use INSERT IGNORE for performance + duplicate protection
        with self.engine.begin() as conn:
            conn.execute(sql, batch)
        # logger.info(f"⚡ Batch Commit: {len(batch)} rows")

    def run_pipeline(self):
        start_time = time.time()
        self.load_registry()
        self.scanners_finished.clear()

        # 1. INITIAL FULL SCAN (Only on first start)
        if self.first_run:
            logger.info("🎬 Initializing ETL Engine v5.0 — Performing structure sync...")
            top_folders = [f for f in self.list_files(ROOT_FOLDER_ID) if f['mimeType'] == 'application/vnd.google-apps.folder']
            with ThreadPoolExecutor(max_workers=32) as executor:
                [executor.submit(self.worker_consumer) for _ in range(24)]
                futures = [executor.submit(self.scanner_producer, f['id'], f['name'], "ROOT") for f in top_folders]
                for f in as_completed(futures): pass
                self.scanners_finished.set()
            self.refresh_summaries()
            self.first_run = False
            self.save_change_token(self.page_token)
            logger.info(f"✅ Initial Sync Complete in {time.time() - start_time:.2f}s. Now entering Reactive Mode.")
            return

        # 2. REACTIVE TARGETED SYNC
        changes = self.get_changes()
        if not changes:
            logger.info("⚡ System Idle... No new changes detected.")
            return

        logger.info(f"🚀 Reactive Trigger! Processing {len(changes)} drive updates...")
        csv_tasks = []
        folders_to_scan = []

        for c in changes:
            if c.get('removed'): continue
            file = c.get('file', {})
            if not file: continue
            
            # Identify what changed
            if file.get('name', '').lower().endswith('.csv'):
                if file['id'] not in self.processed_files:
                    csv_tasks.append({
                        "file_id": file['id'], "file_name": file['name'],
                        "folder_id": "TARGETED", "folder_name": "Reactive",
                        "path": "REACTIVE", "modifiedTime": file.get('modifiedTime')
                    })
            elif file.get('mimeType') == 'application/vnd.google-apps.folder':
                folders_to_scan.append(file)

        # Process new files immediately
        if csv_tasks or folders_to_scan:
            with ThreadPoolExecutor(max_workers=32) as executor:
                # Start workers
                worker_threads = [executor.submit(self.worker_consumer) for _ in range(24)]
                
                # Directly queue new CSVs
                for task in csv_tasks:
                    logger.info(f"🆕 REACTIVE NEW: {task['path']}/{task['file_name']}")
                    self.task_queue.put(task)
                
                # Scan new folders
                for f in folders_to_scan:
                    logger.info(f"📂 REACTIVE SCAN: REACTIVE/{f['name']}")
                    executor.submit(self.scanner_producer, f['id'], f['name'], "REACTIVE")
                
                # Wait for completion
                self.scanners_finished.set()
            
            # Refresh Summary after reactive cycle
            self.refresh_summaries()

        self.save_change_token(self.page_token)
        logger.info(f"✨ Reactive Cycle finished in {time.time() - start_time:.2f}s")

    def refresh_summaries(self):
        """Update the high-speed summary tables for the dashboard."""
        logger.info("📊 Refreshing Dashboard Summaries...")
        try:
            with self.engine.begin() as conn:
                # 1. Global Stats
                res = conn.execute(text("SELECT COUNT(*), COUNT(DISTINCT state), COUNT(DISTINCT category), COUNT(DISTINCT drive_file_id) FROM raw_google_map_drive_data")).fetchone()
                conn.execute(text("""
                    INSERT INTO dashboard_stats_summary_v5 (id, total_records, total_states, total_categories, total_csvs, last_updated)
                    VALUES (1, :total, :states, :cats, :csvs, NOW())
                    ON DUPLICATE KEY UPDATE 
                        total_records=:total, total_states=:states, total_categories=:cats, total_csvs=:csvs, last_updated=NOW()
                """), {"total": res[0], "states": res[1], "cats": res[2], "csvs": res[3]})

                # 2. State-Category summary
                conn.execute(text("DELETE FROM state_category_summary_v5"))
                conn.execute(text("""
                    INSERT INTO state_category_summary_v5 (state, category, record_count)
                    SELECT state, category, COUNT(*) 
                    FROM raw_google_map_drive_data 
                    GROUP BY state, category
                """))
            logger.info("✅ Summaries updated successfully.")
        except Exception as e:
            logger.error(f"❌ Summary Refresh Failed: {e}")

def get_engine():
    return GDriveHighSpeedIngestor()

def start_background_etl():
    ingestor = get_engine()
    def loop():
        while True:
            try:
                ingestor.run_pipeline()
                logger.info("Sleeping for 60s...")
                time.sleep(60)
            except Exception as e:
                logger.error(f"ETL Loop error: {e}")
                time.sleep(10)
    threading.Thread(target=loop, daemon=True).start()

if __name__ == "__main__":
    start_background_etl()
    while True: time.sleep(1)
