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
        print("Checking for duplicate businesses...")
        # Check a sample of duplicates
        query = text("""
            SELECT name, address, COUNT(*) 
            FROM raw_google_map_filewise 
            GROUP BY name, address 
            HAVING COUNT(*) > 1 
            LIMIT 10
        """)
        res = conn.execute(query).fetchall()
        if res:
            print("Duplicates found:")
            for r in res:
                print(f" - {r[0]} | {r[1]} : {r[2]} copies")
        else:
            print("No duplicates found in sample.")
            
except Exception as e:
    print(f"Error: {e}")
