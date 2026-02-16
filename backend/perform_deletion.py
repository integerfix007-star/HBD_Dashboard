"""
Complete database reset script for raw_google_map table.
This drops both old and new tables and clears related caches.
"""
from sqlalchemy import create_engine, text
from config import Config

DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI

def perform_cleanup():
    print("=== COMPLETE DATABASE RESET FOR RAW_GOOGLE_MAP ===")
    engine = create_engine(DATABASE_URI)
    try:
        with engine.begin() as conn:
            # 1. Drop old table if exists
            print("Dropping raw_google_map_data table (if exists)...")
            conn.execute(text("DROP TABLE IF EXISTS raw_google_map_data"))
            print("Done.")
            
            # 2. Drop new table if exists (for fresh start)
            print("Dropping raw_google_map table (if exists)...")
            conn.execute(text("DROP TABLE IF EXISTS raw_google_map"))
            print("Done.")
            
            # 3. Clear file registry
            print("Clearing file_registry...")
            conn.execute(text("DELETE FROM file_registry"))
            print("Done.")
            
            # 4. Clear gdrive_folders cache
            print("Clearing gdrive_folders cache...")
            conn.execute(text("DELETE FROM gdrive_folders"))
            print("Done.")
            
            # 5. Reset sync metadata to start fresh from Feb 2nd
            print("Resetting sync metadata...")
            conn.execute(text("UPDATE gdrive_sync_metadata SET last_sync_time = '2026-02-02T00:00:00Z' WHERE id = 1"))
            print("Done.")
            
            print("\n=== RESET COMPLETE ===")
            print("Run app.py to recreate the raw_google_map table with proper schema.")

    except Exception as e:
        print(f"Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    perform_cleanup()
