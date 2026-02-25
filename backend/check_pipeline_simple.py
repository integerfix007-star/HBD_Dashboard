import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

tables = [
    "raw_google_map_drive_data",
    "validation_raw_google_map",
    "raw_clean_google_map_data",
    "g_map_master_table"
]

with engine.connect() as conn:
    for table in tables:
        try:
            res = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
            print(f"Table {table}: {res[0]} rows")
        except Exception as e:
            print(f"Error checking table {table}: {e}")

    try:
        res = conn.execute(text("SELECT meta_value FROM etl_metadata WHERE meta_key = 'last_processed_id_drive_to_val'")).fetchone()
        print(f"Last processed ID (drive_to_val): {res[0] if res else 'None'}")
        
        res = conn.execute(text("SELECT MAX(id) FROM raw_google_map_drive_data")).fetchone()
        print(f"Max ID in raw_google_map_drive_data: {res[0] if res else 'None'}")
    except Exception as e:
        print(f"Error checking progress: {e}")
