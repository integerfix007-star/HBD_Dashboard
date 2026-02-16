from sqlalchemy import create_engine, text
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT', '3306')
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URI)
table_name = "raw_google_map_drive_data"

try:
    with engine.connect() as conn:
        print("Connecting and executing...")
        sql = text(f"SELECT DISTINCT drive_file_id FROM {table_name} LIMIT 5")
        print(f"SQL Type: {type(sql)}")
        res = conn.execute(sql)
        print("Success! Results:")
        for r in res:
            print(r)
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
