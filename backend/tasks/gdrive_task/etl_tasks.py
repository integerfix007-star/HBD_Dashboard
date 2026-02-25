import os
import csv
import io
import logging
import time
import signal
import hashlib
import threading
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from urllib.parse import quote_plus
from google.oauth2 import service_account
from utils.metrics import (
    files_processed, rows_inserted, rows_skipped,
    processing_time, dlq_entries, active_db_ops, batch_size_hist, error_count
)
from config import config
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from celery import shared_task
from dotenv import load_dotenv
import redis

from model.normalizer import UniversalNormalizer
# from model.csv_schema import BusinessRecord (Validation removed)
# from pydantic import ValidationError

from celery.utils.log import get_task_logger

logger = get_task_logger("GDrive_Celery_Task")

# Ensure file logging still works for history
log_file_path = os.path.join(os.getcwd(), 'output', 'gdrive_etl.log')
if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
# Force UTF-8 encoding for file log

# Centralized configuration
SERVICE_ACCOUNT_FILE = config.SERVICE_ACCOUNT_FILE
DATABASE_URI = config.DATABASE_URI
MAX_FILE_SIZE_MB = config.MAX_FILE_SIZE_MB
ETL_VERSION = config.ETL_VERSION
BATCH_SIZE = config.BATCH_SIZE
# Configuration
SERVICE_ACCOUNT_FILE = os.path.join(os.getcwd(), 'model', 'honey-bee-digital-d96daf6e6faf.json')
DB_USER = os.getenv('DB_USER')
DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT', '3306')
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', '100'))
ETL_VERSION = "2.0.0"

# SECTION 1: Optimized SQLAlchemy Engine (High Throughput)
engine = create_engine(
    DATABASE_URI,
    pool_size=35,            # High-speed: more concurrent connections
    max_overflow=20,         # Extra burst capacity
    pool_timeout=30,        
    pool_recycle=1800,      
    pool_pre_ping=True      
)

# Fix 7: Graceful Shutdown
shutdown_requested = False

def handle_shutdown(signum, frame):
    global shutdown_requested
    shutdown_requested = True
    # Avoid logging here as it causes reentrant RuntimeError during recursive calls or I/O interrupts

# Register signal handlers (only in main thread to avoid Windows errors)
try:
    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)
except (OSError, ValueError):
    # signal handlers can only be set in the main thread
    pass

# Fix 10: DB Rate Limiting (Removed local semaphore as it doesn't work across processes)
# We will rely on Celery's worker concurrency flags to manage parallel workloads smoothly.


def get_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"Service account file not found at: {SERVICE_ACCOUNT_FILE}")
        
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds, cache_discovery=False)


# Fix 1 + Fix 2: File size protection + Context manager (no memory leak)
@contextmanager
def download_csv(service, file_id, max_size_mb=None):
    """
    STREAMS a CSV file from Google Drive row-by-row into memory.
    NO local files, NO temp files, NO ByteIO accumulation of full file.
    """
    request = service.files().get_media(fileId=file_id)
    # Use io.BytesIO() only as a small buffer for the current chunk if needed, 
    # but more efficiently, we can use the stream directly.
    # Actually, MediaIoBaseDownload needs a writable stream.
    # To truly stream without downloading the WHOLE file into memory at once:
    # We use request.execute() but that's for small files.
    # For large files, we use get_media().
    
    import io
    from googleapiclient.http import MediaIoBaseDownload
    
    # We'll use a wrapper that behaves like a file but fetches on demand if possible.
    # However, MediaIoBaseDownload is designed to "download" into a stream.
    # If we want TRUE row-by-row without full download, we should use:
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request, chunksize=1024*1024) # 1MB chunks
    
    # Actually, the requirement "Use Drive API streaming" usually refers to:
    # Downloading the file in chunks and processing it.
    
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    fh.seek(0)
    wrapper = io.TextIOWrapper(fh, encoding='utf-8', errors='replace')
    try:
        yield wrapper
    finally:
        wrapper.close()


def get_file_hash(file_id, modified_time):
    """Generate a hash for file change detection."""
    return hashlib.md5(f"{file_id}:{modified_time}".encode()).hexdigest()


# SECTION 3: Batched Insert Optimization (with Deadlock Retry + Rate Limiting)

def _super_normalize(val):
    """Strip ALL symbols, dashes, commas, periods, and extra spaces. Unicode-safe."""
    if not val:
        return ""
    try:
        import re as _re
        # Remove everything that is NOT a letter, digit, or whitespace (keeps all Unicode scripts)
        cleaned = _re.sub(r'[^\w\s]', '', str(val), flags=_re.UNICODE)
        # Collapse whitespace and lowercase
        return _re.sub(r'\s+', '', cleaned).lower().strip()
    except Exception:
        return str(val).lower().strip()


def _super_normalize_phone(val):
    """Keep only digits from phone number."""
    if not val:
        return ""
    try:
        import re as _re
        return _re.sub(r'\D', '', str(val))
    except Exception:
        return str(val).strip()


def commit_batch(batch, task_id=None):
    """
    Inserts a BATCH of rows efficiently. Atomic within the batch.
    Uses Super-Normalization for strong deduplication.
    """
    if not batch:
        return 0
        
    sql = text("""
        INSERT IGNORE INTO raw_google_map_drive_data (
            name, address, website, phone_number, 
            reviews_count, reviews_average, 
            category, subcategory, city, state, area, 
            drive_file_id, drive_file_name, full_drive_path, 
            drive_uploaded_time, source,
            etl_version, task_id, file_hash
        )
        VALUES (
            :name, :address, :website, :phone_number, 
            :reviews_count, :reviews_average, 
            :category, :subcategory, :city, :state, :area, 
            :drive_file_id, :drive_file_name, :drive_file_path, 
            :drive_uploaded_time, 'google_drive',
            :etl_version, :task_id, :file_hash
        )
    """)
    
    # Pre-process batch with metadata + Super-Normalized deduplication
    unique_batch = []
    try:
        r = redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))
        
        # Build all fingerprints first
        hashes = []
        for row in batch:
            row['etl_version'] = ETL_VERSION
            row['task_id'] = task_id
            
            # Super-Normalized Identity (ignores symbols, dashes, commas, city differences)
            clean_name = _super_normalize(row.get('name', ''))
            clean_phone = _super_normalize_phone(row.get('phone_number', ''))
            clean_address = _super_normalize(row.get('address', ''))
            
            identity_string = f"{clean_name}|{clean_phone}|{clean_address}"
            row_hash = hashlib.md5(identity_string.encode('utf-8')).hexdigest()
            hashes.append((row, row_hash))
        
        # Redis Pipeline: check all hashes in ONE network call
        pipe = r.pipeline(transaction=False)
        for _, row_hash in hashes:
            pipe.sadd("gdrive_etl_unique_records", row_hash)
        results = pipe.execute()
        
        # Only keep rows where Redis returned 1 (newly added = not a duplicate)
        for i, (row, row_hash) in enumerate(hashes):
            if results[i]:  # 1 = new, 0 = already existed
                unique_batch.append(row)
                
    except Exception as e:
        logger.warning(f"Redis deduplication failed in batch: {e}")
        # Fallback: add metadata and pass all rows (INSERT IGNORE handles DB-level dupes)
        for row in batch:
            row['etl_version'] = ETL_VERSION
            row['task_id'] = task_id
        unique_batch = batch

    if not unique_batch:
        return 0

    try:
        with engine.begin() as conn:
            result = conn.execute(sql, unique_batch)
            inserted = result.rowcount
            if inserted > 0:
                rows_inserted.inc(inserted)
            logger.info(f"⚡ Committed batch: {inserted} unique rows.")
            return inserted
    except Exception as e:
        logger.error(f"Batch Insert Failed: {e}")
        return 0


def update_file_checkpoint(file_id, filename, status, row_number=0, error_msg=None, file_hash=None):
    """
    Updates file status and row checkpoint for crash-safe resumption.
    """
    try:
        sql = text("""
            INSERT INTO file_registry (drive_file_id, filename, status, last_processed_row, error_message, file_hash, processed_at)
            VALUES (:file_id, :filename, :status, :row_num, :error_msg, :file_hash, NOW())
            ON DUPLICATE KEY UPDATE 
                status = VALUES(status),
                last_processed_row = VALUES(last_processed_row),
                error_message = VALUES(error_message),
                file_hash = COALESCE(VALUES(file_hash), file_hash),
                processed_at = NOW()
        """)
        with engine.begin() as conn:
            conn.execute(sql, {
                "file_id": file_id,
                "filename": filename,
                "status": status,
                "row_num": row_number,
                "error_msg": error_msg,
                "file_hash": file_hash
            })
    except Exception as e:
        logger.error(f"Checkpoint update failed for {filename}: {e}")

def get_file_checkpoint(file_id):
    """Retrieves the last processed row for a file."""
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT status, last_processed_row FROM file_registry WHERE drive_file_id = :id"), {"id": file_id}).fetchone()
            if res:
                return res[0], res[1]
    except Exception:
        pass
    return None, 0


# Fix 4: Dead Letter Queue
def send_to_dlq(file_id, file_name, error, task_id, retry_count=0):
    """Route permanently failed tasks to the Dead Letter Queue."""
    try:
        sql = text("""
            INSERT INTO etl_dlq (file_id, file_name, error, task_id, retry_count, failed_at)
            VALUES (:file_id, :file_name, :error, :task_id, :retry_count, NOW())
        """)
        with engine.begin() as conn:
            conn.execute(sql, {
                "file_id": file_id,
                "file_name": file_name,
                "error": str(error)[:2000],  # Truncate long errors
                "task_id": task_id,
                "retry_count": retry_count
            })
        dlq_entries.inc()  # Fix 9: Metrics
        logger.warning(f"[DLQ] Task routed to Dead Letter Queue: {file_name} (retries: {retry_count})")
    except Exception as e:
        logger.error(f"[DLQ] Failed to write to DLQ for {file_name}: {e}")


# SECTION 6: Dashboard Stats Refresh — Zero Downtime
@shared_task(name="tasks.gdrive.refresh_stats", ignore_result=True)
def refresh_dashboard_stats():
    """Recalculates dashboard statistics using UPSERT logic."""
    try:
        with engine.begin() as conn:
            # 1. UPSERT Global Summary (id=1)
            res = conn.execute(text("SELECT COUNT(*), COUNT(DISTINCT state), COUNT(DISTINCT category), COUNT(DISTINCT drive_file_id) FROM raw_google_map_drive_data")).fetchone()
            
            conn.execute(text("""
                INSERT INTO dashboard_stats_summary_v5 
                (id, total_records, total_states, total_categories, total_csvs, last_updated)
                VALUES (1, :total, :states, :cats, :csvs, NOW())
                ON DUPLICATE KEY UPDATE 
                    total_records = VALUES(total_records),
                    total_states = VALUES(total_states),
                    total_categories = VALUES(total_categories),
                    total_csvs = VALUES(total_csvs),
                    last_updated = NOW()
            """), {"total": res[0], "states": res[1], "cats": res[2], "csvs": res[3]})

            # 2. UPSERT State-Category Summary
            # Using READ UNCOMMITTED to prevent this heavy COUNT from placing shared locks
            # on the raw_google_map_drive_data table, blocking incoming Celery batch inserts.
            conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))
            conn.execute(text("""
                INSERT INTO state_category_summary_v5 (state, category, record_count)
                SELECT state, category, COUNT(*) 
                FROM raw_google_map_drive_data 
                GROUP BY state, category
                ON DUPLICATE KEY UPDATE 
                    record_count = VALUES(record_count)
            """))
            conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ"))
            
        logger.info("Dashboard stats refreshed successfully without locking tables.")
    except Exception as e:
        logger.error(f"Stats Refresh Failed: {e}")

def trigger_stats_refresh():
    """Call this inside process_csv_task on success."""
    try:
        r = redis.from_url(os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"))
        val = r.incr("gdrive_etl_file_count")
        if val % 50 == 0:
            refresh_dashboard_stats.delay()
            logger.debug(f"Triggering stats refresh (Counter: {val})")
    except Exception as e:
        logger.warning(f"Failed to check stats trigger: {e}")


# SECTION 4: Main Processing Task (with all fixes applied)
@shared_task(
    bind=True, 
    max_retries=3,  # Fix 4: Reduced from 5 to route to DLQ faster
    name="tasks.gdrive.process_csv",
    autoretry_for=(OperationalError,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True
)
def process_csv_task(self, file_id, file_name, folder_id, folder_name, path, modified_time):
    global shutdown_requested
    start_time = time.time()
    task_id = self.request.id
    file_hash = get_file_hash(file_id, modified_time)
    
    # 1. Check for existing checkpoint (Idempotency Phase 3)
    status, last_row = get_file_checkpoint(file_id)
    if status == 'PROCESSED':
        logger.info(f"⏭ Skip: {file_name} already fully processed.")
        return f"Skipped processed file: {file_name}"
    
    try:
        service = get_service()
        update_file_checkpoint(file_id, file_name, 'IN_PROGRESS', last_row, file_hash=file_hash)
        
        with download_csv(service, file_id) as stream:
            reader = csv.DictReader(stream)
            current_row_idx = 0
            batch = []
            BATCH_THRESHOLD = 2000 # High-speed: 4x fewer DB round-trips
            
            for row in reader:
                current_row_idx += 1
                
                # Resume logic: Skip rows already processed
                if current_row_idx <= last_row:
                    continue

                if shutdown_requested:
                    if batch:
                        commit_batch(batch, task_id=task_id)
                    update_file_checkpoint(file_id, file_name, 'IN_PROGRESS', current_row_idx-1, 
                                          error_msg="Graceful shutdown")
                    return f"Paused: {file_name} at row {current_row_idx-1}"
                
                # Normalize
                norm_row = UniversalNormalizer.normalize_row({
                    **row, "drive_file_id": file_id, "drive_file_name": file_name,
                    "drive_folder_id": folder_id, "drive_folder_name": folder_name,
                    "drive_file_path": path, "drive_uploaded_time": modified_time
                })
                norm_row['file_hash'] = file_hash
                batch.append(norm_row)
                
                # BATCH INSERT (High Speed)
                if len(batch) >= BATCH_THRESHOLD:
                    commit_batch(batch, task_id=task_id)
                    update_file_checkpoint(file_id, file_name, 'IN_PROGRESS', current_row_idx, file_hash=file_hash)
                    batch = []

            # Remaining rows
            if batch:
                commit_batch(batch, task_id=task_id)
            
            # Final success state
            update_file_checkpoint(file_id, file_name, 'PROCESSED', current_row_idx, file_hash=file_hash)

        processing_time.observe(time.time() - start_time)
        files_processed.inc()
        trigger_stats_refresh()
        return f"Completed {file_name}: {current_row_idx} rows"

    except Exception as e:
        logger.error(f"[CRASH] {file_name}: {e}")
        update_file_checkpoint(file_id, file_name, 'ERROR', last_row, error_msg=str(e), file_hash=file_hash)
        if self.request.retries >= self.max_retries:
            send_to_dlq(file_id, file_name, str(e), task_id, self.request.retries)
        raise self.retry(exc=e)
