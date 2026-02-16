import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD') 
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT', '3306')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def run_sql(sql):
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
            print(f"Success: {sql}")
    except Exception as e:
        print(f"Skipped/Error: {sql} | {str(e)[:100]}")

run_sql("CREATE INDEX idx_file_id ON raw_google_map_filewise (file_id)")
run_sql("CREATE INDEX idx_business_dedupe ON raw_google_map_filewise (name(50), address(50))")
print("Done.")
