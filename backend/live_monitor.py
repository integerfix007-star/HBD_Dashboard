import time
from sqlalchemy import text, create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

print("--- 📊 DATABASE LIVE MONITOR ---")
print("Watching for real-time inventory growth...")

last_f_count = 0
last_v_count = 0

try:
    while True:
        with engine.connect() as conn:
            f_count = conn.execute(text("SELECT COUNT(*) FROM raw_google_map")).scalar()
            v_count = conn.execute(text("SELECT COUNT(*) FROM gdrive_inventory_folders")).scalar()
            
            diff_f = f_count - last_f_count if last_f_count > 0 else 0
            diff_v = v_count - last_v_count if last_v_count > 0 else 0
            
            print(f"[{time.strftime('%H:%M:%S')}] Files: {f_count} (+{diff_f}) | Folders: {v_count} (+{diff_v})")
            
            last_f_count = f_count
            last_v_count = v_count
            
        time.sleep(5)
except KeyboardInterrupt:
    print("\nMonitor stopped.")
