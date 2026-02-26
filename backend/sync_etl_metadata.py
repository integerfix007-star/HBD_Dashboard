import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv('DB_USER')
db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT', '3306')

DATABASE_URI = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
engine = create_engine(DATABASE_URI)

with engine.begin() as conn:
    # Get the max raw_id from the clean table to resume correctly
    res = conn.execute(text("SELECT MAX(raw_id) FROM raw_clean_google_map_data"))
    max_id = res.fetchone()[0] or 0
    
    conn.execute(text("""
        INSERT INTO etl_metadata (meta_key, meta_value) 
        VALUES ('last_processed_id', :val) 
        ON DUPLICATE KEY UPDATE meta_value = :val
    """), {"val": str(max_id)})
    print(f"✅ etl_metadata updated: last_processed_id = {max_id}")
