from sqlalchemy import create_engine, text
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
db_user = os.getenv('DB_USER')
db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or '')
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_port = os.getenv('DB_PORT')

engine = create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')

fixes = {
    "Andhrapradesh": "Andhra Pradesh",
    "Arunachalpradesh": "Arunachal Pradesh",
    "Uttarpradesh": "Uttar Pradesh",
    "Madhyapradesh": "Madhya Pradesh",
    "Himachalpradesh": "Himachal Pradesh",
    "Westbengal": "West Bengal",
    "Tamilnadu": "Tamil Nadu",
}

with engine.begin() as conn:
    for old, new in fixes.items():
        res = conn.execute(text("UPDATE raw_google_map_drive_data SET state = :new WHERE state = :old"), {"new": new, "old": old})
        print(f"Fixed {old} -> {new}: {res.rowcount} rows")
    
    # Fuzzy fix for Arunachal
    res = conn.execute(text("UPDATE raw_google_map_drive_data SET state = 'Arunachal Pradesh' WHERE state LIKE 'Arunachalpradesh%'"))
    print(f"Fixed Arunachal (wildcard): {res.rowcount} rows")
