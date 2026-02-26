import os
import sys
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

table_name = sys.argv[1] if len(sys.argv) > 1 else 'raw_google_map_drive_data'

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

try:
    with engine.connect() as conn:
        row = conn.execute(text(f"SHOW CREATE TABLE {table_name}")).fetchone()
        print(row[1])
except Exception as e:
    print(f"Error: {e}")
