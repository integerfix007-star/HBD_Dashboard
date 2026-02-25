import os
import re
import io
import csv
import time
import random
import hashlib
import logging
import threading
import queue
import redis
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

from .normalizer import UniversalNormalizer
from utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

load_dotenv()

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s')
logger = logging.getLogger("GDriveETLv4")

# Suppress noisy Google API warnings
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
import warnings
warnings.filterwarnings("ignore", message="file_cache is only supported with oauth2client<4.0.0")

# Configuration Constants
# Fix 6: Move ROOT_FOLDER_ID to environment variable
ROOT_FOLDER_ID = os.getenv('GDRIVE_ROOT_FOLDER_ID', '1ltTYjekxZsk2CdF20tSk1B2FnRn4119E')
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
        # Producer uses a standard pool since it's threaded, not gevent
        self.engine = create_engine(DATABASE_URI, pool_size=35, max_overflow=25, pool_pre_ping=True, pool_recycle=3600, isolation_level="READ COMMITTED")
        self.table_name = "raw_google_map_drive_data"
        self.task_queue = queue.Queue(maxsize=100)
        self.folder_registry = {}  # Changed to Dict {folder_id: modified_time}
        self.processed_files = {}  # Fix 8: Dict {file_id: file_hash} instead of set
        self.shutdown_event = threading.Event()
        self.scanners_finished = threading.Event()
        self._tls = threading.local()
        self.first_run = True  # Track if we need an initial full scan
        self.page_token = None
        # Circuit breaker for Google Drive API calls
        self.api_breaker = CircuitBreaker(name="gdrive_api")
        
        # Stats & Heartbeat
        self.stats_lock = threading.Lock()
        self.total_scanned_folders = 0
        self.total_skipped_folders = 0
        self.total_dispatched_files = 0

    def shutdown(self):
        """Signal the ingestor to stop."""
        self.shutdown_event.set()

    def get_service(self):
        if not hasattr(self._tls, 'service'):
            self._tls.service = build('drive', 'v3', credentials=self.creds, cache_discovery=False)
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

    @staticmethod
    def get_file_hash(file_id, modified_time):
        """Generate a hash for file change detection."""
        return hashlib.md5(f"{file_id}:{modified_time}".encode()).hexdigest()

    def load_registry(self):
        """Load already processed file IDs + hashes, folder timestamps."""
        logger.info("Loading Registry Checkpoints...")
        with self.engine.connect() as conn:
            # Load file hashes and status for high-speed change detection
            files = conn.execute(text("SELECT drive_file_id, file_hash, status FROM file_registry"))
            self.processed_files = {row[0]: {"hash": row[1], "status": row[2]} for row in files}
            
            # Load Folder Registry (ID -> ModifiedTime)
            folders = conn.execute(text("SELECT folder_id, drive_modified_at FROM drive_folder_registry"))
            self.folder_registry = {row[0]: row[1] for row in folders}
            
            # Load Token
            res = conn.execute(text("SELECT meta_value FROM etl_metadata WHERE meta_key='last_change_token'"))
            row = res.fetchone()
            if row: self.page_token = row[0] if row else None

        logger.info(f"Registry loaded: {len(self.processed_files)} files, {len(self.folder_registry)} folders.")

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
        try:
            with self.engine.begin() as conn:
                sql = text("""
                    INSERT INTO drive_folder_registry (folder_id, folder_name, drive_modified_at, csv_count, status, scanned_at) 
                    VALUES (:id, :name, :mod, :count, 'DONE', NOW()) 
                    ON DUPLICATE KEY UPDATE 
                        drive_modified_at=VALUES(drive_modified_at), 
                        csv_count=VALUES(csv_count), 
                        status='DONE',
                        scanned_at=NOW()
                """)
                conn.execute(sql, {"id": folder_id, "name": folder_name, "mod": modified_at, "count": csv_count})
            
            # Update In-Memory Cache
            self.folder_registry[folder_id] = modified_at
        except Exception as e:
            logger.error(f"Failed to register folder {folder_name}: {e}")

    @retry_on_429
    def list_files(self, parent_id):
        # Circuit breaker + rate limit protected API call
        def _list():
            return self.get_service().files().list(
                q=f"'{parent_id}' in parents and trashed=false", 
                fields="files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc",
                pageSize=1000 
            ).execute().get('files', [])
        try:
            return self.api_breaker.call(_list)
        except CircuitBreakerOpenError as e:
            logger.warning(f"Circuit breaker OPEN, skipping list_files for {parent_id}: {e}")
            return []

    def scanner_producer(self, folder_id, folder_name, path=""):
        if self.shutdown_event.is_set(): return
        
        # 1. Fetch items (Already sorted by modifiedTime DESC in API call)
        items = self.list_files(folder_id)
        
        # Separate Folders and Files to guarantee processing order
        folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
        csv_files = [item for item in items if item['name'].lower().endswith('.csv')]
        
        # Process NEWEST CSV FILES first
        folder_skipped = 0
        folder_dispatched = 0
        
        for item in csv_files:
            if self.shutdown_event.is_set(): break
            
            # High-Speed Change Detection (Phase 3) using Cached Registry
            current_hash = self.get_file_hash(item['id'], item.get('modifiedTime', ''))
            cached = self.processed_files.get(item['id'], {})
            existing_hash = cached.get('hash')
            status = cached.get('status')
            
            if status == 'PROCESSED' and existing_hash == current_hash:
                folder_skipped += 1
                continue
                
            # New, Modified, or Partial file -> Dispatch (Phase 2 & 3)
            from tasks.gdrive_task.etl_tasks import process_csv_task
            process_csv_task.delay(
                file_id=item['id'], 
                file_name=item['name'],
                folder_id=folder_id, 
                folder_name=folder_name,
                path=f"{path}/{folder_name}", 
                modified_time=item.get('modifiedTime')
            )
            folder_dispatched += 1

        # Then recursively scan NEWEST SUBFOLDERS (Phase 2)
        for folder in folders:
            if self.shutdown_event.is_set(): break
            self.scanner_producer(folder['id'], folder['name'], f"{path}/{folder_name}")
            
        with self.stats_lock:
            self.total_scanned_folders += 1
            self.total_dispatched_files += folder_dispatched
            
        # Register folder scan as done
        mod_time = items[0].get('modifiedTime') if items else datetime.utcnow().isoformat() + "Z"
        self.register_folder(folder_id, folder_name, mod_time, len(csv_files))

    # REMOVED: download_csv, worker_consumer, process_file, commit_batch
    # These are now handled by Celery in tasks/gdrive_task/etl_tasks.py

    def run_pipeline(self):
        start_time = time.time()
        self.load_registry()
        
        logger.info("="*60)
        logger.info(f"📊 [STARTUP SUMMARY]")
        logger.info(f"   - Processed Files in DB: {len(self.processed_files)}")
        logger.info(f"   - Registered Folders:    {len(self.folder_registry)}")
        logger.info("="*60)
        
        self.scanners_finished.clear()
        
        # Reset Stats for new run
        with self.stats_lock:
            self.total_scanned_folders = 0
            self.total_skipped_folders = 0
            self.total_dispatched_files = 0
            
        # 1. INITIAL FULL SCAN (Only on first start)
        if self.first_run:
            # Reset Celery Aggregated Counters in Redis ONLY on first startup
            try:
                r = redis.Redis(host='localhost', port=6379, db=0)
                r.set('celery_files_processed', 0)
                r.set('celery_rows_inserted', 0)
                logger.info("🔄 Redis Counters Reset (files & rows)")
            except Exception as e:
                logger.warning(f"⚠️ Failed to reset Redis counters: {e}")

            logger.info("🎬 Initializing GDrive Orchestrator v6.0 (Celery Mode)...")
            top_folders = [f for f in self.list_files(ROOT_FOLDER_ID) if f['mimeType'] == 'application/vnd.google-apps.folder']
            
            # We still use a ThreadPool for SCANNING (iterating folders), but not for processing
            with ThreadPoolExecutor(max_workers=32) as executor:
                futures = [executor.submit(self.scanner_producer, f['id'], f['name'], "ROOT") for f in top_folders]
                for f in as_completed(futures): pass
                self.scanners_finished.set()
            
            # Removed redundant Producer-side stats refresh (handled by Celery now)
            self.first_run = False
            self.save_change_token(self.page_token)
            logger.info("="*60)
            logger.info(f"✅ Initial Scan Complete in {time.time() - start_time:.2f}s")
            logger.info(f"   - Total Folders Scanned: {self.total_scanned_folders}")
            logger.info(f"   - Total Folders Skipped: {self.total_skipped_folders}")
            logger.info(f"   - Total Files Dispatched: {self.total_dispatched_files}")
            logger.info("="*60)
            return

        # 2. REACTIVE TARGETED SYNC
        changes = self.get_changes()
        if not changes:
            logger.info("⚡ System Idle... No new changes detected.")
            return

        logger.info(f"🚀 Reactive Trigger! Disptaching {len(changes)} updates to Celery...")
        
        from tasks.gdrive_task.etl_tasks import process_csv_task
        
        folders_to_scan = []

        for c in changes:
            if c.get('removed'): continue
            file = c.get('file', {})
            if not file: continue
            
            # Identify what changed
            if file.get('name', '').lower().endswith('.csv'):
                if file['id'] not in self.processed_files:
                     logger.debug(f"🆕 REACTIVE TASK: {file['name']}")
                     process_csv_task.delay(
                        file_id=file['id'], 
                        file_name=file['name'],
                        folder_id="TARGETED", 
                        folder_name="Reactive",
                        path="REACTIVE", 
                        modified_time=file.get('modifiedTime')
                     )
            elif file.get('mimeType') == 'application/vnd.google-apps.folder':
                folders_to_scan.append(file)
        
        # Deduplicate folders to prevent parallel scans of the same folder
        if folders_to_scan:
            seen_ids = set()
            unique_folders = []
            for f in folders_to_scan:
                if f['id'] not in seen_ids:
                    seen_ids.add(f['id'])
                    unique_folders.append(f)
            folders_to_scan = unique_folders
            logger.info(f"📂 Scanning {len(folders_to_scan)} unique reactive folders...")

            with ThreadPoolExecutor(max_workers=8) as executor:
                for f in folders_to_scan:
                    executor.submit(self.scanner_producer, f['id'], f['name'], "REACTIVE")
            
        self.save_change_token(self.page_token)
        logger.info(f"✨ Reactive Cycle dispatched in {time.time() - start_time:.2f}s")


class ValidationCleaningProcessor:
    """
    🛡️ Continuous Validation & Cleaning Layer
    Processes raw_google_map_drive_data -> validation_raw_google_map -> raw_clean_google_map_data
    Ensures zero data loss, multilingual safety, and logical duplicate detection.
    """
    def __init__(self, engine, shutdown_event):
        self.engine = engine
        self.shutdown_event = shutdown_event
        self.batch_size = 10000 # High-speed: process 10k rows per cycle

    def get_last_processed_id(self):
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT meta_value FROM etl_metadata WHERE meta_key='last_processed_id'"))
                row = res.fetchone()
                return int(row[0]) if row and str(row[0]).isdigit() else 0
        except Exception:
            return 0

    def update_last_processed_id(self, last_id):
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO etl_metadata (meta_key, meta_value) 
                    VALUES ('last_processed_id', :val) 
                    ON DUPLICATE KEY UPDATE meta_value = :val
                """), {"val": str(last_id)})
        except Exception as e:
            logger.error(f"Failed to update last_processed_id: {e}")

    def log_validation_batch(self, summary):
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO data_validation_log 
                    (total_processed, missing_count, valid_count, duplicate_count, cleaned_count, timestamp)
                    VALUES (:total, :missing, :valid, :duplicate, :cleaned, NOW())
                """), summary)
        except Exception as e:
            logger.error(f"Failed to log validation batch: {e}")

    def is_missing(self, val):
        return val is None or str(val).strip() == ""

    def validate_row(self, row):
        # Mandatory fields for STRUCTURED check (Multilingual Safe)
        mandatory_fields = ["name", "address", "phone_number", "city", "state", "category"]
        missing = [f for f in mandatory_fields if self.is_missing(row.get(f))]
        
        is_structured = len(missing) == 0
        
        # Format checks for VALID check
        invalid_fields = []
        
        # Phone (Phase 7): Numeric only, 8-18 digits
        raw_phone = str(row.get('phone_number', '') or '')
        clean_phone = re.sub(r'\D', '', raw_phone)
        if not (self.is_missing(clean_phone)) and not re.match(r'^\d{8,18}$', clean_phone):
            invalid_fields.append("phone_number")
        elif self.is_missing(clean_phone):
            if "phone_number" not in missing:
                missing.append("phone_number")
            
        # Website: Must contain "." if present
        website = str(row.get('website', '') or '').strip()
        if website and '.' not in website:
            invalid_fields.append("website")
            
        is_valid = len(invalid_fields) == 0 and is_structured
        
        return is_structured, is_valid, missing, invalid_fields, clean_phone

    def check_duplicates_batch(self, signatures, conn):
        """Batch check signatures against the clean table."""
        if not signatures: return set()
        
        # We check exactly against the composite index for speed
        check_query = text("""
            SELECT name, phone_number, address FROM raw_clean_google_map_data 
            WHERE (phone_number, name, address) IN :sigs
        """)
        
        # Format for Tuple IN clause in MySQL
        # Construct raw string for IN clause as fallback or use parameter binding
        # Faster approach: Hash-based duplicate check using MD5 in Python
        # Instead of slow tuple IN clause, we hash signatures and compare sets
        
        results = set()
        sig_list = list(signatures)
        
        # Build hash lookup for existing clean data
        for i in range(0, len(sig_list), 2000):
            batch = sig_list[i:i+2000]
            # Build WHERE clause with OR conditions for speed
            conditions = []
            params = {}
            for idx, (phone, name, addr) in enumerate(batch):
                conditions.append(f"(phone_number = :p{idx} AND LOWER(TRIM(name)) = :n{idx})")
                params[f"p{idx}"] = phone
                params[f"n{idx}"] = name
            
            if not conditions:
                continue
                
            query = f"SELECT LOWER(TRIM(name)) as n, phone_number as p, LOWER(TRIM(address)) as a FROM raw_clean_google_map_data WHERE {' OR '.join(conditions)}"
            try:
                rows = conn.execute(text(query), params).fetchall()
                for r in rows:
                    results.add((str(r[1]), str(r[0]), str(r[2])))
            except Exception as e:
                logger.warning(f"Duplicate check sub-batch failed: {e}")
        return results

    def start_pipeline(self):
        """Main loop for the validation thread."""
        last_id = self.get_last_processed_id()
        logger.info(f"🛡️ Validation Processor Started from ID: {last_id}")
        
        while not self.shutdown_event.is_set():
            try:
                # Use a SINGLE connection for the entire cycle (fetch + check + write)
                with self.engine.begin() as conn:
                    # READ UNCOMMITTED: prevents locking raw table during read
                    conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))
                    
                    # 1. Fetch batch — only needed columns (faster than SELECT *)
                    rows = conn.execute(text("""
                        SELECT id, name, address, website, phone_number, 
                               reviews_count, reviews_average, category, subcategory, 
                               city, state, area, created_at
                        FROM raw_google_map_drive_data 
                        WHERE id > :last_id 
                        ORDER BY id ASC 
                        LIMIT :limit
                    """), {"last_id": last_id, "limit": self.batch_size}).fetchall()
                
                    if not rows:
                        conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
                        if self.shutdown_event.wait(timeout=10):
                            break
                        continue

                    batch_summary = {
                        "total": 0,
                        "missing": 0,
                        "valid": 0,
                        "duplicate": 0,
                        "cleaned": 0
                    }
                    
                    current_max_id = last_id
                    
                    # 2. Process batch in memory
                    validation_batch = []
                    invalid_audit_batch = []
                    clean_data_batch = []
                    master_data_batch = []
                    
                    # Pre-calculate signatures for bulk duplicate check
                    batch_rows = []
                    signatures = set()
                    
                    for row_obj in rows:
                        row = row_obj._asdict() if hasattr(row_obj, '_asdict') else row_obj._mapping
                        batch_rows.append(row)
                        current_max_id = max(current_max_id, row['id'])
                        
                        # Pre-validate and extract phone
                        raw_phone = str(row.get('phone_number', '') or '')
                        clean_phone = re.sub(r'\D', '', raw_phone)
                        norm_name = str(row.get('name', '') or '').strip().lower()
                        norm_addr = str(row.get('address', '') or '').strip().lower()
                        
                        signatures.add((clean_phone, norm_name, norm_addr))

                    # Bulk Duplicate Check (same connection, no overhead)
                    existing_sigs = self.check_duplicates_batch(signatures, conn)
                    
                    # Switch back to safe mode for writes
                    conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"))

                    for row in batch_rows:
                        batch_summary["total"] += 1
                        is_structured, is_valid, missing_list, invalid_list, clean_phone = self.validate_row(row)
                        
                        norm_name = str(row.get('name', '') or '').strip().lower()
                        norm_addr = str(row.get('address', '') or '').strip().lower()
                        sig = (clean_phone, norm_name, norm_addr)
                        is_duplicate = sig in existing_sigs if is_structured else False

                        # Determine status
                        if not is_structured: status = "MISSING"; batch_summary["missing"] += 1
                        elif is_duplicate: status = "DUPLICATE"; batch_summary["duplicate"] += 1
                        elif not is_valid: status = "INVALID"
                        else: status = "VALID"

                        # 3. Queue for Validation Table
                        validation_batch.append({
                            "raw_id": row['id'], "name": row['name'], "address": row['address'], "website": row['website'],
                            "phone_number": row['phone_number'], "reviews_count": row.get('reviews_count', 0),
                            "reviews_avg": row.get('reviews_average', 0.00), "category": row['category'],
                            "subcategory": row['subcategory'], "city": row['city'], "state": row['state'],
                            "area": row['area'], "created_at": row.get('created_at') or datetime.now(),
                            "status": status, "missing": ",".join(missing_list) if missing_list else None,
                            "invalid": ",".join(invalid_list) if invalid_list else None
                        })

                        # 4. Queue for Invalid Audit
                        if status in ["MISSING", "INVALID"]:
                            invalid_audit_batch.append({
                                "raw_id": row['id'], "name": row['name'], "address": row['address'], "website": row['website'],
                                "phone": clean_phone, "bank": row['phone_number'],
                                "reviews": row.get('reviews_count', 0), "avg": row.get('reviews_average', 0.00),
                                "cat": row['category'], "sub": row['subcategory'], "city": row['city'],
                                "state": row['state'], "area": row['area'], "label": status,
                                "missing": ",".join(missing_list) if missing_list else None,
                                "invalid": ",".join(invalid_list) if invalid_list else None,
                                "reason": f"Missing: {','.join(missing_list)} | Invalid: {','.join(invalid_list)}"
                            })

                        # 5. Queue for Production
                        if status == "VALID":
                            batch_summary["valid"] += 1
                            clean_data_batch.append({
                                "raw_id": row['id'], "name": str(row['name']).strip(), "address": str(row['address']).strip(),
                                "website": str(row['website']).lower().strip() if row['website'] else None,
                                "phone": clean_phone, "reviews": row.get('reviews_count', 0), "avg": row.get('reviews_average', 0.00),
                                "cat": row['category'], "sub": row['subcategory'], "city": row['city'],
                                "state": row['state'], "area": row['area'], "created": row.get('created_at') or datetime.now()
                            })
                            master_data_batch.append({
                                "name": str(row['name']).strip(), "address": str(row['address']).strip(),
                                "website": str(row['website']).lower().strip() if row['website'] else None,
                                "phone": clean_phone, "reviews": row.get('reviews_count', 0), "avg": row.get('reviews_average', 0.00),
                                "cat": row['category'], "sub": row['subcategory'], "city": row['city'],
                                "state": row['state'], "area": row['area'], "created": row.get('created_at') or datetime.now()
                            })
                            batch_summary["cleaned"] += 1

                    # 6. Execute Batch Writes (same transaction — atomic)
                    if validation_batch:
                        conn.execute(text("""
                            INSERT INTO validation_raw_google_map 
                            (raw_id, name, address, website, phone_number, reviews_count, reviews_avg, 
                             category, subcategory, city, state, area, created_at, 
                             validation_status, missing_fields, invalid_format_fields, processed_at)
                            VALUES 
                            (:raw_id, :name, :address, :website, :phone_number, :reviews_count, :reviews_avg,
                             :category, :subcategory, :city, :state, :area, :created_at,
                             :status, :missing, :invalid, NOW())
                            ON DUPLICATE KEY UPDATE validation_status = VALUES(validation_status), processed_at = NOW()
                        """), validation_batch)

                    if invalid_audit_batch:
                        conn.execute(text("""
                            INSERT INTO invalid_google_map_data 
                            (raw_id, name, address, website, phone_number, bank_number, 
                             reviews_count, reviews_avg, category, subcategory, city, state, area,
                             validation_label, missing_fields, invalid_format_fields, error_reason, created_at)
                            VALUES 
                            (:raw_id, :name, :address, :website, :phone, :bank,
                             :reviews, :avg, :cat, :sub, :city, :state, :area,
                             :label, :missing, :invalid, :reason, NOW())
                        """), invalid_audit_batch)

                    if clean_data_batch:
                        conn.execute(text("""
                            INSERT IGNORE INTO raw_clean_google_map_data 
                            (raw_id, name, address, website, phone_number, reviews_count, reviews_avg,
                             category, subcategory, city, state, area, created_at)
                            VALUES (:raw_id, :name, :address, :website, :phone, :reviews, :avg, :cat, :sub, :city, :state, :area, :created)
                        """), clean_data_batch)
                        
                    if master_data_batch:
                        conn.execute(text("""
                            INSERT IGNORE INTO g_map_master_table 
                            (name, address, website, phone_number, reviews_count, reviews_avg, category, subcategory, city, state, area, created_at)
                            VALUES (:name, :address, :website, :phone, :reviews, :avg, :cat, :sub, :city, :state, :area, :created)
                        """), master_data_batch)

                # 7. Finalize batch
                self.update_last_processed_id(current_max_id)
                self.log_validation_batch(batch_summary)
                last_id = current_max_id
                
                logger.info(f"🛡️ Batch Complete: Processed {batch_summary['total']} rows. Last ID: {last_id}")

            except Exception as e:
                logger.error(f"🛡️ Validation Loop Error: {e}")
                if self.shutdown_event.wait(timeout=10):
                    break

def get_engine():
    return GDriveHighSpeedIngestor()

def start_background_etl():
    """Started by app.py to orchestrate the scanning."""
    ingestor = get_engine()
    
    # Start Drive Scanner Thread
    def scanner_loop():
        while not ingestor.shutdown_event.is_set():
            try:
                ingestor.run_pipeline()
                logger.info("Scanner sleeping for 30s...")
                if ingestor.shutdown_event.wait(timeout=30):
                    break
            except Exception as e:
                logger.error(f"Scanner Loop error: {e}")
                time.sleep(10)
    
    t_scanner = threading.Thread(target=scanner_loop, name="ScannerThread", daemon=True)
    t_scanner.start()

    # Start Validation & Cleaning Thread
    validator = ValidationCleaningProcessor(ingestor.engine, ingestor.shutdown_event)
    t_validator = threading.Thread(target=validator.start_pipeline, name="ValidatorThread", daemon=True)
    t_validator.start()

    return ingestor

if __name__ == "__main__":
    start_background_etl()
    while True: time.sleep(1)
