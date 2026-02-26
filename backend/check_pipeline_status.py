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

with engine.connect() as conn:
    raw = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).fetchone()[0]
    clean = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data")).fetchone()[0]
    gmap_master = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).fetchone()[0]
    meta = conn.execute(text("SELECT meta_value FROM etl_metadata WHERE meta_key='last_processed_id'")).fetchone()
    
    print(f"Raw Count: {raw}")
    print(f"Clean Count: {clean}")
    print(f"G-Map Master Count: {gmap_master}")
    print(f"Last Processed ID: {meta[0] if meta else 'None'}")
