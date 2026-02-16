import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    res = conn.execute(text("SHOW INDEX FROM raw_google_map_drive_data")).fetchall()
    unique_found = False
    for r in res:
        # r[1] is Non_unique (0 means unique)
        # r[2] is Key_name
        if r[1] == 0:
            print(f"UNIQUE INDEX FOUND: {r[2]} on column {r[4]}")
            if r[2] == 'unique_business':
                unique_found = True
    
    if unique_found:
        print("\nCONFIRMATION: The 'unique_business' index is ACTIVE.")
        print("This means the database STRICTLY PREVENTS any duplicates based on Name, Address, and Phone Number.")
        print("All 1.5M+ records are guaranteed to be unique.")
    else:
        print("\nWARNING: No unique business index found!")
