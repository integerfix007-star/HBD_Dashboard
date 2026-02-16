from sqlalchemy import create_engine, text
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_user=os.getenv('DB_USER')
db_pass=quote_plus(os.getenv('DB_PASSWORD_PLAIN') or '')
db_host=os.getenv('DB_HOST')
db_name=os.getenv('DB_NAME')
db_port=os.getenv('DB_PORT')

engine=create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')

with engine.connect() as conn:
    print("Checking drive_folder_registry schema...")
    res = conn.execute(text('DESCRIBE drive_folder_registry')).fetchall()
    columns = [r[0] for r in res]
    
    if 'drive_modified_at' not in columns:
        print("Adding drive_modified_at...")
        conn.execute(text('ALTER TABLE drive_folder_registry ADD COLUMN drive_modified_at VARCHAR(100)'))
    
    if 'csv_count' not in columns:
        print("Adding csv_count...")
        conn.execute(text('ALTER TABLE drive_folder_registry ADD COLUMN csv_count INT DEFAULT 0'))
        
    if 'status' not in columns:
        print("Adding status...")
        conn.execute(text('ALTER TABLE drive_folder_registry ADD COLUMN status VARCHAR(50) DEFAULT "Completed"'))
    
    # Also ensure raw_google_map_drive_data has the Unique constraint if not present
    print("Checking unique constraint on raw_google_map_drive_data...")
    try:
        # Check if index exists first to avoid error
        idx_res = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data WHERE Key_name = 'unique_business'")).fetchall()
        if not idx_res:
            print("Creating unique_business index...")
            conn.execute(text("CREATE UNIQUE INDEX unique_business ON raw_google_map_drive_data (name, address, phone_number)"))
        else:
            print("unique_business index already exists.")
    except Exception as e:
        print(f"Index check/creation error: {e}")

    # Add etl_metadata table for Reactive Sync
    print("Checking etl_metadata table...")
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS etl_metadata (
            meta_key VARCHAR(50) PRIMARY KEY,
            meta_value VARCHAR(255),
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """))

    print("Migration complete.")
