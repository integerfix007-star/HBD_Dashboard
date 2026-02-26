"""
🗑️ HIGH-PERFORMANCE CLEANER (v2): Delete raw duplicates via Temporary Table
Removed prefix lengths from GROUP BY as it's not supported in that clause.
"""
from sqlalchemy import create_engine, text
import urllib.parse, os, time
from dotenv import load_dotenv

load_dotenv()
pw = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "darshit@1912"))
user = os.getenv("DB_USER", "local_dashboard")
host = os.getenv("DB_HOST", "127.0.0.1")
db = os.getenv("DB_NAME", "local_dashboard")
port = os.getenv("DB_PORT", "3306")

engine = create_engine(
    f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db}?charset=utf8mb4",
    connect_args={"read_timeout": 600, "write_timeout": 600}
)

def clean_raw_duplicates():
    print(f"🚀 Starting High-Performance Cleanup...")
    start_time = time.time()
    
    with engine.begin() as conn:
        conn.execute(text("SET SESSION sql_mode=''"))
        conn.execute(text("SET SESSION innodb_lock_wait_timeout=600"))
        
        # 1. Create a temporary table of IDs to KEEP 
        print("📁 1/3: Creating index of IDs to keep...")
        conn.execute(text("DROP TEMPORARY TABLE IF EXISTS tmp_ids_to_keep"))
        
        # Use simple column names in GROUP BY
        conn.execute(text("""
            CREATE TEMPORARY TABLE tmp_ids_to_keep (
                id BIGINT PRIMARY KEY
            ) AS
            SELECT MIN(id) as id
            FROM raw_google_map_drive_data
            GROUP BY name, phone_number, city, address
        """))
        
        # 2. Statistics
        total_before = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).fetchone()[0]
        to_keep = conn.execute(text("SELECT COUNT(*) FROM tmp_ids_to_keep")).fetchone()[0]
        to_delete = total_before - to_keep
        print(f"📊 Rows before: {total_before}, To keep: {to_keep}, To delete: {to_delete}")

        if to_delete <= 0:
            print("✅ No duplicates found.")
            return

        # 3. Fast delete using LEFT JOIN where keep.id IS NULL
        print(f"🗑️ 2/3: Executing multi-table DELETE (removing {to_delete} duplicates)...")
        conn.execute(text("""
            DELETE t1 FROM raw_google_map_drive_data t1
            LEFT JOIN tmp_ids_to_keep t2 ON t1.id = t2.id
            WHERE t2.id IS NULL
        """))
        
        print("📁 3/3: Cleanup complete.")

    duration = time.time() - start_time
    print(f"✨ SUCCESS! Cleanup completed in {duration:.2f}s.")

if __name__ == "__main__":
    try:
        clean_raw_duplicates()
    except Exception as e:
        print(f"❌ High-Performance cleanup failed: {e}")
