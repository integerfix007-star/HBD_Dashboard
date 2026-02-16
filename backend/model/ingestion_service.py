import os
import io
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables (DB credentials)
load_dotenv()

# --- CONFIGURATION ---
SERVICE_ACCOUNT_FILE = 'service_account.json' # Path to your GDrive service account key
ROOT_FOLDER_NAME = 'Top cities'               # The parent folder to monitor
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD_PLAIN')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

class GDriveIngestor:
    def __init__(self):
        self.scopes = ['https://www.googleapis.com/auth/drive.readonly']
        self.creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=self.scopes
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        self.engine = create_engine(DATABASE_URI)

    def find_folder_id(self, folder_name):
        """Finds the folder ID by name."""
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])
        return files[0]['id'] if files else None

    def get_file_registry(self):
        """Fetches list of already processed file IDs."""
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT drive_file_id FROM file_registry WHERE status = 'completed'"))
            return {row[0] for row in result}

    def register_file(self, file_id, filename, city, category, status='pending', error=None):
        """Updates the file registry."""
        query = text("""
            INSERT INTO file_registry (drive_file_id, filename, city, category, status, error_message)
            VALUES (:id, :name, :city, :cat, :status, :err)
            ON DUPLICATE KEY UPDATE status=:status, error_message=:err
        """)
        with self.engine.begin() as conn:
            conn.execute(query, {"id": file_id, "name": filename, "city": city, "cat": category, "status": status, "err": error})

    def download_csv(self, file_id):
        """Downloads CSV content into a pandas memory buffer."""
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh

    def process_cities_folder(self, root_id):
        """Recursively iterates through city folders and processes CSVs."""
        processed_files = self.get_file_registry()
        
        # 1. List all sub-folders (Cities)
        query = f"'{root_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        city_folders = self.service.files().list(q=query, fields="files(id, name)").execute().get('files', [])

        for folder in city_folders:
            city_name = folder['name']
            print(f"Checking City: {city_name}")

            # 2. List all CSVs in the City folder
            query = f"'{folder['id']}' in parents and mimeType = 'text/csv' and trashed = false"
            csv_files = self.service.files().list(q=query, fields="files(id, name)").execute().get('files', [])

            for csv in csv_files:
                file_id = csv['id']
                filename = csv['name']
                category = filename.replace('.csv', '').strip().lower()

                if file_id in processed_files:
                    print(f"  - Skipping {filename} (Already processed)")
                    continue

                print(f"  - Ingesting: {filename} (Category: {category})")
                
                try:
                    # Download and load
                    csv_buffer = self.download_csv(file_id)
                    df = pd.read_csv(csv_buffer)

                    # Append Metadata Columns
                    df['source_city'] = city_name
                    df['source_category'] = category
                    df['drive_file_id'] = file_id

                    # Ingest into DB (Append mode)
                    # Note: Columns in CSV should match or be handled by the mapping below
                    # We only keep columns that exist in our target table to prevent errors
                    target_table = 'raw_ingestions'
                    df.to_sql(target_table, con=self.engine, if_exists='append', index=False)

                    # Mark as completed
                    self.register_file(file_id, filename, city_name, category, status='completed')
                    print(f"  - Success: {filename}")

                except Exception as e:
                    print(f"  - Error processing {filename}: {str(e)}")
                    self.register_file(file_id, filename, city_name, category, status='failed', error=str(e))

if __name__ == "__main__":
    ingestor = GDriveIngestor()
    root_id = ingestor.find_folder_id(ROOT_FOLDER_NAME)
    
    if root_id:
        print(f"Starting ETL Pipeline for Root ID: {root_id}")
        ingestor.process_cities_folder(root_id)
    else:
        print(f"Could not find root folder: {ROOT_FOLDER_NAME}")
