import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'scripts', 'gdrive_etl', 'honey-bee-digital-d96daf6e6faf.json')

def get_all_csvs_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query, 
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    files = results.get('files', [])
    csv_files = []
    for f in files:
        if f['mimeType'] == 'text/csv':
            csv_files.append(f)
        elif f['mimeType'] == 'application/vnd.google-apps.folder':
            csv_files.extend(get_all_csvs_in_folder(service, f['id']))
    return csv_files

if __name__ == "__main__":
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    service = build('drive', 'v3', credentials=creds)
    # Himachal Pradesh ID
    hp_id = "1fYgSnkNXcdlEkqyD6dtAxU5--Iq5u5Na"
    csvs = get_all_csvs_in_folder(service, hp_id)
    print(f"Found {len(csvs)} CSVs in Himachal.")
    for c in csvs[:5]:
        print(f"- {c['name']}")
