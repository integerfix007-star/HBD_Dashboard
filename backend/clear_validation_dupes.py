"""
🗑️ Remove DUPLICATE rows from validation_raw_google_map
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

def clear_duplicates():
    print(f"🚀 Cleaning validation_raw_google_map...")
    start_time = time.time()
    
    with engine.begin() as conn:
        conn.execute(text("SET SESSION sql_mode=''"))
        
        # Check count first
        count_res = conn.execute(text("SELECT COUNT(*) FROM validation_raw_google_map WHERE validation_status = 'DUPLICATE'"))
        count = count_res.fetchone()[0]
        print(f"📊 Found {count} rows with status 'DUPLICATE'")
        
        if count > 0:
            print(f"🗑️ Deleting {count} rows...")
            res = conn.execute(text("DELETE FROM validation_raw_google_map WHERE validation_status = 'DUPLICATE'"))
            print(f"✅ Deleted {res.rowcount} rows.")
        else:
            print("✅ No rows with status 'DUPLICATE' found.")

    duration = time.time() - start_time
    print(f"✨ Task completed in {duration:.2f}s.")

if __name__ == "__main__":
    clear_duplicates()
