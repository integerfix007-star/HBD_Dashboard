from sqlalchemy import text, create_engine
import os
from dotenv import load_dotenv
load_dotenv()
engine = create_engine(f'mysql+mysqlconnector://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}')
print('Files Ingested Today:', engine.connect().execute(text('SELECT COUNT(*) FROM raw_google_map WHERE DATE(ingestion_timestamp) = CURDATE()')).scalar())
print('Folders Discovered Today:', engine.connect().execute(text('SELECT COUNT(*) FROM gdrive_inventory_folders WHERE DATE(modified_time) = CURDATE()')).scalar())
