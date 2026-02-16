import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_user = os.getenv('DB_USER')
db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or '')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
engine = create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}')

files_to_check = [
    'google_maps_data_Popular_Computer_Training_Institutes_Hojai_Assam.csv',
    'google_maps_data_Popular_Computer_Training_Institutes_Sivasagar_Assam.csv'
]

print("Checking ingestion status for specific files...")
with engine.connect() as conn:
    for file_name in files_to_check:
        query = text("SELECT count(*), city, state, category FROM raw_google_map WHERE file_name = :fname GROUP BY city, state, category")
        res = conn.execute(query, {"fname": file_name}).fetchall()
        if res:
            for row in res:
                print(f"✅ FOUND: {file_name}")
                print(f"   - Count: {row[0]} records")
                print(f"   - City: {row[1]}")
                print(f"   - State: {row[2]}")
                print(f"   - Category: {row[3]}")
        else:
            print(f"❌ NOT FOUND: {file_name}")
