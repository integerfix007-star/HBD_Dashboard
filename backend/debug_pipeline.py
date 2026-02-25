import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    for table in ["raw_google_map_drive_data", "validation_raw_google_map", "raw_clean_google_map_data"]:
        print(f"\nColumns in {table}:")
        res = conn.execute(text(f"DESC {table}")).fetchall()
        for row in res:
            print(f"  {row[0]} ({row[1]})")
