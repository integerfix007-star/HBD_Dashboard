import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.begin() as conn:
    print("Adding indexes to raw_google_map_drive_data...")
    try:
        conn.execute(text("CREATE INDEX idx_state ON raw_google_map_drive_data (state)"))
        print("Index on state added.")
    except Exception as e:
        print(f"Index on state already exists or error: {e}")

    try:
        conn.execute(text("CREATE INDEX idx_category ON raw_google_map_drive_data (category)"))
        print("Index on category added.")
    except Exception as e:
        print(f"Index on category already exists or error: {e}")
    
    try:
        conn.execute(text("CREATE INDEX idx_drive_file_id ON raw_google_map_drive_data (drive_file_id)"))
        print("Index on drive_file_id added.")
    except Exception as e:
        print(f"Index on drive_file_id already exists or error: {e}")

    print("Indexes check complete.")
