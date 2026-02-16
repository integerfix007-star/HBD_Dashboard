import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    try:
        res = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).fetchone()
        print(f"Total records in raw_google_map_drive_data: {res[0]}")
    except Exception as e:
        print(f"Error checking raw_google_map_drive_data: {e}")

    try:
        res = conn.execute(text("SELECT COUNT(*) FROM raw_google_map")).fetchone()
        print(f"Total records in raw_google_map: {res[0]}")
    except Exception as e:
        print(f"Error checking raw_google_map: {e}")
