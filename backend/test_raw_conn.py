import os
import time
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
# Use the raw password from env if available
raw_pass = os.getenv('DB_PASSWORD') 

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT', '3306')

print(f"Attempting connection to {DB_HOST}...")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{raw_pass}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

try:
    start = time.time()
    with engine.connect() as conn:
        print(f"Connected in {time.time()-start:.2f}s")
        res = conn.execute(text("SELECT 1")).scalar()
        print(f"Query Result: {res}")
            
except Exception as e:
    print(f"Error: {e}")
