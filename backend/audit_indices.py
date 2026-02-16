import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    print("Checking indexes on raw_google_map_drive_data...")
    res = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data")).fetchall()
    indices = [r[2] for r in res]
    cols = [r[4] for r in res]
    
    print(f"Indices: {set(indices)}")
    print(f"Indexed Columns: {set(cols)}")
    
    # Check if we have a unique index on (name, address)
    res = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data WHERE Non_unique = 0")).fetchall()
    uniques = [r[2] for r in res]
    print(f"Unique Indices: {set(uniques)}")
