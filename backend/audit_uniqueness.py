import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

db_pass = quote_plus(os.getenv('DB_PASSWORD_PLAIN') or "")
DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{db_pass}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    print("Checking for duplicate business entries...")
    # This query finds if there are any (name, address, phone) groups with more than 1 record
    # We use a subquery to avoid loading 1.5M rows
    sql = """
    SELECT COUNT(*) FROM (
        SELECT name, address, phone_number 
        FROM raw_google_map_drive_data 
        GROUP BY name, address, phone_number 
        HAVING COUNT(*) > 1
    ) AS dupes
    """
    res = conn.execute(text(sql)).fetchone()
    dupe_groups = res[0]
    
    total_res = conn.execute(text("SELECT COUNT(*) FROM raw_google_map_drive_data")).fetchone()
    total_count = total_res[0]
    
    print(f"Total Records: {total_count}")
    print(f"Number of groups that have duplicates: {dupe_groups}")
    
    if dupe_groups == 0:
        print("RESULT: All data is 100% unique based on Name, Address, and Phone Number.")
    else:
        print(f"RESULT: There are {dupe_groups} sets of businesses that appear more than once.")
