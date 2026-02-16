import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = os.getenv('DB_PORT', '3306')

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

try:
    print("Connecting...")
    with engine.connect() as conn:
        print("Connected. Querying states...")
        res = conn.execute(text("SELECT DISTINCT state FROM raw_google_map_filewise LIMIT 10"))
        print("States:", [r[0] for r in res])
except Exception as e:
    print(f"Error: {e}")
