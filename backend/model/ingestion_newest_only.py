import os
import io
import re
import time
import pandas as pd
import hashlib
from sqlalchemy import create_engine, text
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(BASE_DIR, 'honey-bee-digital-d96daf6e6faf.json') 
# Your Root Folder ID (New root from user)
ROOT_FOLDER_ID = "1ltTYjekxZsk2CdF20tSk1B2FnRn4119E" 

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"

EXCLUDED_FOLDERS = {
    'darshit', 'riyaz', 'krunali', 'jahnavi', 'harikesh pratap verma', 'thomas', 'ayush', 'anushk', 'hetvi',
    'aarya', 'rohit', 'vedanshi', 'fujel', 'google map data', 'top cities', 'uncategorized', 'cleaned', 'latest', 'all_districts'
}

KNOWN_PLACES = {
    'mandi', 'solan', 'shimla', 'dharamshala', 'kullu', 'baddi', 'hamirpur', 'una', 
    'palampur', 'paonta sahib', 'nahan', 'sundarnagar', 'chamba', 'santokhgarh', 
    'anantnag', 'nurpur', 'srinagar', 'alleppey', 'arsikere', 'bilaspur', 'rohru',
    'mehatpur basdehra', 'nalagarh', 'dalhousie', 'ghumarwin', 
    'jammu', 'kashmir', 'kangra', 'manali', 'leh', 'ladakh', 'amritsar', 'ludhiana',
    'jalandhar', 'chandigarh', 'pathankot', 'hoshairpur', 'batala', 'fazilka',
    'soyibug', 'sopur', 'manjeri', 'malappuram', 'kozhikode', 'calicut', 'kannur', 
    'thrissur', 'palakkad', 'ernakulam', 'kochi', 'alappuzha', 'kollam', 
    'thiruvananthapuram', 'trivandrum', 'idukki', 'kottayam', 'pathanamthitta', 
    'wayanad', 'kasaragod', 'delhi', 'new delhi', 'karol bagh'
}

REGIONS = {
    'himachal pradesh', 'kerala', 'jammu kashmir', 'jammu and kashmir', 
    'srinagar', 'jammu', 'kashmir', 'punjab', 'delhi', 'ladakh', 'haryana'
}

# Common words that signify a category rather than a city
CATEGORY_KEYWORDS = {
    'service', 'services', 'restaurant', 'restaurants', 'dentist', 'dentists', 'jobs', 'training', 'spa', 'shop', 'shops', 'store', 'stores', 
    'clinic', 'hospital', 'school', 'college', 'academy', 'gym', 'bank', 'atm', 
    'hotel', 'resort', 'cafe', 'parlour', 'agency', 'center', 'doctor', 'villa',
    'automotive', 'architectural', 'banquet', 'burger', 'car_hire', 'beauty', 
    'massage', 'parts', 'furniture', 'hardware', 'electronics', 'grocery', 
    'bakery', 'takeaway', 'beverage', 'jewellery', 'lunch', 'spots', 'south_indian', 
    'amusement', 'pure_veg', 'popular', 'snack', 'quick_bite', 'computer', 'institutes',
    'massage', 'parts', 'furniture', 'hardware', 'electronics', 'grocery', 
    'bakery', 'takeaway', 'beverage', 'jewellery', 'lunch', 'spots', 'south_indian', 
    'amusement', 'pure_veg', 'popular', 'snack', 'quick_bite', 'computer', 'institutes',
    'ac_service', 'top_dentist', 'juice', 'resort', 'tax consultants', 'tax_consultants',
    'courier', 'couriers', 'transporters', 'transporter', 'car_rental', 'car_rentals',
    'travel', 'travels', 'hospital', 'hospitals'
}

class GDriveSmartIngestor:
    def __init__(self, service_account_path=SERVICE_ACCOUNT_FILE):
        # We need full drive access to create folders and upload files
        self.scopes = ['https://www.googleapis.com/auth/drive']
        if not os.path.exists(service_account_path):
            raise FileNotFoundError(f"Service account file not found: {service_account_path}")
            
        self.creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=self.scopes
        )
        self.service = build('drive', 'v3', credentials=self.creds)
        self.engine = create_engine(DATABASE_URI)
        self.folder_cache = {} 
        self.resolution_cache = {} # Cache for (city, category, path) by parent_folder_id


    def get_processed_files(self):
        """Returns a set of Google Drive File IDs already processed."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT drive_file_id FROM file_registry WHERE status = 'completed'"))
                return {row[0] for row in result}
        except Exception:
            return set()

    def get_last_sync_time(self):
        """Fetches the last successful sync time from the database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT last_sync_time FROM gdrive_sync_metadata WHERE id = 1"))
                row = result.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            print(f"Metadata table check failed: {e}")
        return "2026-01-30T00:00:00Z"

    def update_last_sync_time(self, timestamp):
        """Updates the last sync time in the database."""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO gdrive_sync_metadata (id, last_sync_time) 
                    VALUES (1, :ts) 
                    ON DUPLICATE KEY UPDATE last_sync_time = :ts
                """), {"ts": timestamp})
        except Exception as e:
            print(f"Error updating sync metadata: {e}")

    def get_folder_info(self, folder_id):
        """Fetches folder name and parents with caching."""
        if folder_id in self.folder_cache:
            return self.folder_cache[folder_id]
        try:
            meta = self.service.files().get(fileId=folder_id, fields="id, name, parents").execute()
            self.folder_cache[folder_id] = meta
            return meta
        except Exception:
            return None

    def get_root_city_folder(self, file_meta):
        """Finds which root folder (direct child of ROOT_FOLDER_ID) this file belongs to."""
        curr_id = file_meta.get('parents', [None])[0]
        if not curr_id: return None
        
        path_cache = []
        depth = 0
        while curr_id and curr_id != ROOT_FOLDER_ID and depth < 8:
            info = self.get_folder_info(curr_id)
            if not info: break
            path_cache.insert(0, info)
            parents = info.get('parents')
            if not parents: break
            
            if ROOT_FOLDER_ID in parents:
                # This folder is a direct child of root!
                return info
            
            curr_id = parents[0]
            depth += 1
        return None

    def resolve_city_and_category(self, csv_meta, parents):
        """Pure Algorithmic Resolution: 
           Uses position of folder names in filename to determine City/Category.
           - Folder at start of filename -> Category (e.g. Transporters_Ghumarwin)
           - Folder later in filename -> City (e.g. Dentist_Baddi)
        """
        filename = csv_meta['name']
        fn_lower = filename.lower().replace('.csv', '')
        
        # 1. Resolve Path Folders
        parent_id = csv_meta.get('parents', [None])[0]
        if parent_id and parent_id in self.resolution_cache:
            path_folders = self.resolution_cache[parent_id]
        else:
            path_folders = []
            if parents:
                curr_id = parents[0]
                depth_limit = 8
                while curr_id and curr_id != ROOT_FOLDER_ID and depth_limit > 0:
                    info = self.get_folder_info(curr_id)
                    if not info: break
                    path_folders.insert(0, info['name'])
                    curr_id = info.get('parents', [None])[0]
                    depth_limit -= 1
            if parent_id:
                self.resolution_cache[parent_id] = path_folders
        
        full_path = "/".join(path_folders)
        
        # 2. Prepare Data
        # Filter path: exclude known junk folders if any (user strict excluded only)
        clean_folders = [p for p in path_folders if p.lower() not in EXCLUDED_FOLDERS and not p.lower().startswith('cleaned_')]
        
        # Clean filename parts
        raw_parts = re.split(r'[_ ]+', fn_lower)
        ignore_words = {'google', 'maps', 'data', 'cleaned', 'latest', 'csv', 'of', 'in'}
        fn_parts = [p for p in raw_parts if p and p not in ignore_words]
        
        found_city = None
        found_cat = None
        
        # 3. Positional Logic
        # Try to match folders to filename parts
        matched_indices = []
        
        for folder in clean_folders:
            f_lower = folder.lower()
            # Check if folder name matches a part (approximate check)
            for idx, part in enumerate(fn_parts):
                if part in f_lower or f_lower in part: 
                     # Only accept if robust match (length > 2)
                    if len(part) > 2:
                        matched_indices.append((idx, folder))
                        break
        
        if matched_indices:
            # Sort by index
            matched_indices.sort(key=lambda x: x[0])
            first_match_idx, first_match_folder = matched_indices[0]
            
            if first_match_idx == 0:
                # Folder is at START -> It is a Category
                found_cat = first_match_folder
                
                # City is the remaining parts that are NOT part of the folder name
                # Heuristic: Remove words that look like the folder name
                folder_words = set(re.split(r'[_ ]+', found_cat.lower()))
                remaining = []
                for p in fn_parts:
                    if p.lower() not in folder_words:
                        remaining.append(p)
                    # Once we have skipped the prefix, we might want to keep everything else?
                    # But 'Security System' might match 'Security' and 'System'.
                    # Let's just filter out folder words spread across the filename? 
                    # Risk: 'Manali' folder and 'Manali' in filename.
                
                # Better approach for Prefix Category:
                # Consume parts from the start that match folder words
                # e.g. fn_parts = [Security, System, Rohru...]
                # folder_words = {security, system}
                # Check 0: Security in folder_words? Yes. Consume.
                # Check 1: System in folder_words? Yes. Consume.
                # Check 2: Rohru in folder_words? No. Stop consuming.
                
                start_idx = 0
                for part in fn_parts:
                    if part.lower() in folder_words or any(w in part.lower() for w in folder_words):
                        start_idx += 1
                    else:
                        break
                
                found_city = " ".join(fn_parts[start_idx:])
            else:
                # Folder is NOT at start -> It is a City (or Locality)
                found_city = first_match_folder
                
                # Category is the Before
                before_parts = fn_parts[:first_match_idx]
                found_cat = " ".join(before_parts)
        
        else:
            # Fallback: No folder matched filename parts.
            # This happens when:
            # 1. Filename is simple category like "Doctor.csv" in folder "Anantnag"
            # 2. Folder is a city name, filename is category
            
            # NEW LOGIC: Use last non-excluded folder as City, filename as Category
            if clean_folders:
                # Last clean folder is likely the City (e.g., "Anantnag")
                found_city = clean_folders[-1]
                # Filename becomes Category (e.g., "Doctor")
                found_cat = " ".join(fn_parts) if fn_parts else "General"
            elif len(fn_parts) >= 2:
                found_cat = fn_parts[0]
                found_city = " ".join(fn_parts[1:])
            elif fn_parts:
                found_cat = "General"
                found_city = fn_parts[0]
            else:
                found_cat = "General"
                found_city = "Unknown"

        # Final Sanitization
        final_city = found_city.strip().replace('_', ' ').title() if found_city else "Unknown"
        final_cat = found_cat.strip().replace('_', ' ').title() if found_cat else "General"
        
        # Allow specific overrides for State/District names if they end up as City?
        # User complained about "Himachal Pradesh". 
        # With "Transporters_Ghumarwin_Himachal_Pradesh", "Transporters" matches index 0.
        # City = "Ghumarwin Himachal Pradesh". This is acceptable (Specific + Region).
        
        if final_cat.lower() == final_city.lower():
            final_cat = "General"

        return final_city, final_cat, full_path

    def ingest_single_csv(self, csv_meta, processed_files):
        """Downloads and ingests a single CSV file."""
        file_id = csv_meta['id']
        filename = csv_meta['name']
        
        if file_id in processed_files:
            return False

        # Resolve Smart City and Category
        city_name, category_name, full_path = self.resolve_city_and_category(csv_meta, csv_meta.get('parents'))
        
        # Parse modified time from GDrive (ISO string)
        drive_modified_str = csv_meta.get('modifiedTime', '')
        drive_modified_dt = None
        if drive_modified_str:
            try:
                drive_modified_dt = datetime.fromisoformat(drive_modified_str.replace('Z', '+00:00'))
            except:
                pass

        print(f"\n[INGESTING] {city_name} / {category_name}")
        print(f" 📂 Path: {full_path}")
        print(f" 📄 File: {filename}")
        print(f" 🕒 Drive Time: {drive_modified_str}")

        try:
            # Download
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            
            # Process Data
            df = pd.read_csv(fh)
            df = df.fillna("")

            # Normalize columns
            column_mapper = {
                'name': 'name', 'Name': 'name', 'business_name': 'name',
                'address': 'address', 'Address': 'address',
                'website': 'website', 'Website': 'website',
                'phone_number': 'phone_number', 'Contact': 'phone_number', 'contact': 'phone_number',
                'Review Count': 'reviews_count', 'reviews_count': 'reviews_count',
                'Review Avg': 'reviews_average', 'reviews_average': 'reviews_average', 'rating': 'reviews_average',
                'category': 'category', 'Category': 'category', 'categories': 'category',
                'subcategory': 'subcategory', 'Sub-Category': 'subcategory',
                'city': 'city', 'City': 'city', 'state': 'state', 'State': 'state'
            }

            df = df.rename(columns={k: v for k, v in column_mapper.items() if k in df.columns})
            
            # --- STRICT FILTERING DISABLED ---
            # Previously filtered rows by city match, but this was too aggressive
            # for folders like Anantnag where filenames are categories (Doctor.csv, School.csv)
            # The source_city column already tracks which folder the data came from.
            # If needed, filtering can be done at dashboard level.


            target_columns = ['name', 'address', 'website', 'phone_number', 'reviews_count', 
                             'reviews_average', 'category', 'subcategory', 'city', 'state']
            for col in target_columns:
                if col not in df.columns:
                    df[col] = ""
            
            # Smart Mappings
            df['source_city'] = city_name
            df['source_category'] = category_name
            df['drive_file_id'] = file_id
            df['drive_modified_at'] = drive_modified_dt
            df['drive_path'] = full_path
            
            all_possible_db_cols = target_columns + ['source_city', 'source_category', 'drive_file_id', 'drive_modified_at', 'drive_path']
            df = df[[col for col in df.columns if col in all_possible_db_cols]]

            # Bulk Insert
            if not df.empty:
                df.to_sql('raw_google_map', con=self.engine, if_exists='append', index=False)
            
            # Log Success
            with self.engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO file_registry (drive_file_id, filename, city, category, status)
                    VALUES (:id, :name, :city, :cat, 'completed')
                    ON DUPLICATE KEY UPDATE status='completed', filename=:name, city=:city
                """), {"id": file_id, "name": filename, "city": city_name, "cat": category_name})
            
            print(f" ✅ Success: Loaded {len(df)} records.")
            return True
        except Exception as e:
            print(f"      Error: {e}")
            return False



    def run_fast_sync(self):
        """Full recursive sync: scans ALL folders from root, finds CSVs, and ingests based on date filter."""
        try:

            with self.engine.begin() as conn:
                row = conn.execute(text("SELECT last_sync_time FROM gdrive_sync_metadata WHERE id=1")).fetchone()
                last_sync = row[0] if row else '2026-02-02T00:00:00Z'
                processed_rows = conn.execute(text("SELECT drive_file_id FROM file_registry")).fetchall()
                processed_files = {r[0] for r in processed_rows}

            print(f"\n--- GDrive Full Recursive Sync (Since {last_sync}) ---")
            print(f"Root Folder ID: {ROOT_FOLDER_ID}")
            
            # 1. Recursively scan ALL folders from root to find CSVs
            def scan_folder_recursive(folder_id, depth=0, max_depth=10):
                """Recursively scan a folder for CSVs and subfolders."""
                if depth > max_depth:
                    return []
                
                all_csvs = []
                page_token = None
                
                while True:
                    # Query for both folders and CSVs
                    query = f"'{folder_id}' in parents and trashed = false"
                    results = self.service.files().list(
                        q=query,
                        fields="nextPageToken, files(id, name, mimeType, modifiedTime, createdTime, parents)",
                        pageSize=1000,
                        pageToken=page_token
                    ).execute()
                    
                    items = results.get('files', [])
                    for item in items:
                        if item['mimeType'] == 'text/csv':
                            # Check BOTH modifiedTime AND createdTime
                            # This captures files that were:
                            # 1. Modified since last_sync (content changed)
                            # 2. Created/Added since last_sync (new file or moved/copied)
                            mod_time = item.get('modifiedTime', '')
                            created_time = item.get('createdTime', '')
                            if mod_time >= last_sync or created_time >= last_sync:
                                all_csvs.append(item)
                        elif item['mimeType'] == 'application/vnd.google-apps.folder':
                            # Also check if folder itself is new
                            folder_created = item.get('createdTime', '')
                            if folder_created >= last_sync:
                                print(f"  📁 NEW FOLDER: {item['name']} (Created: {folder_created})")
                            # Recurse into subfolder regardless
                            all_csvs.extend(scan_folder_recursive(item['id'], depth + 1, max_depth))
                    
                    page_token = results.get('nextPageToken')
                    if not page_token:
                        break
                
                return all_csvs
            
            print("Scanning all folders recursively...")
            all_csvs = scan_folder_recursive(ROOT_FOLDER_ID)
            
            if not all_csvs:
                print("No new CSV modifications detected.")
                return

            print(f"Detected {len(all_csvs)} modified CSVs. Grouping by root city...")
            
            # 2. Group CSVs by Root City Folder
            city_groups = {} # folder_id -> {'info': folder_meta, 'csvs': []}
            unknown_csvs = []
            
            for csv in all_csvs:
                root_folder = self.get_root_city_folder(csv)
                if root_folder:
                    fid = root_folder['id']
                    if fid not in city_groups:
                        city_groups[fid] = {'info': root_folder, 'csvs': []}
                    city_groups[fid]['csvs'].append(csv)
                else:
                    unknown_csvs.append(csv)
            
            # 3. Sort Cities by Date (matching UI priority)
            sorted_cities = sorted(city_groups.values(), key=lambda x: x['info'].get('modifiedTime', ''), reverse=True)
            
            any_ingested = False
            new_latest_sync = last_sync
            
            for group in sorted_cities:
                root_info = group['info']
                root_name = root_info['name']
                print(f"\n[CITY GROUP] {root_name} (Updated: {root_info.get('modifiedTime')})")
                
                # Sort CSVs within the group by date
                group['csvs'].sort(key=lambda x: x.get('modifiedTime', ''), reverse=True)
                
                for csv_meta in group['csvs']:
                    if self.ingest_single_csv(csv_meta, processed_files):
                        any_ingested = True
                        if csv_meta['modifiedTime'] > new_latest_sync:
                            new_latest_sync = csv_meta['modifiedTime']
            
            # 4. Process unknown/direct files (if any)
            if unknown_csvs:
                print(f"\n[MISC] Processing {len(unknown_csvs)} files outside root folders...")
                for csv_meta in unknown_csvs:
                    if self.ingest_single_csv(csv_meta, processed_files):
                        any_ingested = True

            # Update Watermark
            with self.engine.begin() as conn:
                conn.execute(text("UPDATE gdrive_sync_metadata SET last_sync_time = :t WHERE id = 1"), 
                             {"t": new_latest_sync})
            
            if not any_ingested:
                print("Sync run finished. All files were already up-to-date.")
                
        except Exception as e:
            print(f"Sync Error: {e}")
            import traceback
            traceback.print_exc()

def run_ingestion(service_account_path=SERVICE_ACCOUNT_FILE):
    ingestor = GDriveSmartIngestor(service_account_path=service_account_path)
    ingestor.run_fast_sync()

if __name__ == "__main__":
    run_ingestion()
