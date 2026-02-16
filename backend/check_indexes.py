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

try:
    with engine.connect() as conn:
        print("--- TABLE INDEXES ---")
        res = conn.execute(text("SHOW INDEX FROM raw_google_map_filewise")).fetchall()
        for r in res:
            # Key_name is index 2, Column_name is index 4, Non_unique is index 1
            print(f"Index: {r[2]} | Column: {r[4]} | Unique: {r[1] == 0}")
            
except Exception as e:
    print(f"Error: {e}")
