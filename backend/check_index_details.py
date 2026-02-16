import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    print("--- Indexes for raw_google_map_drive_data ---")
    res = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data")).fetchall()
    for r in res:
        print(r)
    
    print("\n--- Recent 5 records ---")
    res = conn.execute(text("SELECT id, name, drive_file_name FROM raw_google_map_drive_data ORDER BY id DESC LIMIT 5")).fetchall()
    for r in res:
        print(r)
