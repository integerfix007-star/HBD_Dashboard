import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv
import json

load_dotenv()

DB_USER = os.getenv('DB_USER')
DB_PASS = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"

def get_samples():
    engine = create_engine(DATABASE_URI)
    with engine.connect() as conn:
        query = text("SELECT name, address, phone_number, city, state, category, source FROM raw_google_map WHERE name IS NOT NULL ORDER BY ingestion_timestamp DESC LIMIT 5")
        results = conn.execute(query).fetchall()
        for row in results:
            print(f"Name: {row.name}")
            print(f"Address: {row.address}")
            print(f"Phone: {row.phone_number}")
            print(f"Location: {row.city}, {row.state}")
            print(f"Category: {row.category}")
            print(f"Source: {row.source}")
            print("-" * 30)


if __name__ == "__main__":
    get_samples()
