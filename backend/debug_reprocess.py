"""Quick check: Why are files getting re-processed?"""
from sqlalchemy import create_engine, text
import urllib.parse, os
from dotenv import load_dotenv

load_dotenv()
pw = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "darshit@1912"))
user = os.getenv("DB_USER", "local_dashboard")
host = os.getenv("DB_HOST", "127.0.0.1")
db = os.getenv("DB_NAME", "local_dashboard")
port = os.getenv("DB_PORT", "3306")

engine = create_engine(f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db}?charset=utf8mb4")

with engine.connect() as conn:
    conn.execute(text("SET SESSION sql_mode=''"))

    # 1. File Registry stats
    total = conn.execute(text("SELECT COUNT(*) FROM file_registry")).fetchone()[0]
    processed = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status='PROCESSED'")).fetchone()[0]
    in_prog = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status='IN_PROGRESS'")).fetchone()[0]
    error = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE status='ERROR'")).fetchone()[0]
    null_hash = conn.execute(text("SELECT COUNT(*) FROM file_registry WHERE file_hash IS NULL")).fetchone()[0]

    print("=" * 80)
    print("FILE REGISTRY STATUS")
    print("=" * 80)
    print(f"  Total files:     {total}")
    print(f"  PROCESSED:       {processed}")
    print(f"  IN_PROGRESS:     {in_prog}")
    print(f"  ERROR:           {error}")
    print(f"  NULL file_hash:  {null_hash}")

    # 2. Check: does ANY drive_file_id appear in raw_data table with MORE rows
    #    than the CSV should have? This indicates re-processing
    print("\n" + "=" * 80)
    print("TOP FILES BY ROW COUNT (possible re-ingestion)")
    print("=" * 80)

    multi = conn.execute(text("""
        SELECT drive_file_id, drive_file_name, COUNT(*) as row_count 
        FROM raw_google_map_drive_data 
        WHERE drive_file_id IS NOT NULL
        GROUP BY drive_file_id
        ORDER BY row_count DESC 
        LIMIT 15
    """)).fetchall()

    for r in multi:
        fid = r[0][:20] if r[0] else "---"
        fname = (r[1] or "---")[:45]
        print(f"  {fname:<47} rows={r[2]:>5}  file_id={fid}")

    # 3. Check: Are businesses in the duplicated groups coming from the SAME file or DIFFERENT files?
    print("\n" + "=" * 80)
    print("EXAMPLE: SBI ATM in Mandla — where do the 18 duplicates come from?")
    print("=" * 80)
    
    sbi = conn.execute(text("""
        SELECT r.id, r.name, r.city, r.category, r.drive_file_name, r.drive_file_id, r.address
        FROM raw_google_map_drive_data r
        WHERE LOWER(r.name) LIKE 'sbi atm%' 
          AND r.city = 'Mandla'
          AND r.category = 'atm'
        ORDER BY r.id
    """)).fetchall()

    print(f"\n  Found {len(sbi)} raw rows for 'SBI ATM' in Mandla (category=atm):\n")
    print(f"  {'ID':<10}{'File Name':<45}{'Address (first 40)'}")
    print(f"  {'-'*95}")
    
    file_names_seen = {}
    for r in sbi:
        fname = (r[4] or "---")[:43]
        addr = (r[6] or "---")[:40]
        print(f"  {r[0]:<10}{fname:<45}{addr}")
        file_names_seen[r[4]] = file_names_seen.get(r[4], 0) + 1

    print(f"\n  File breakdown:")
    for fname, count in sorted(file_names_seen.items(), key=lambda x: -x[1]):
        print(f"    {fname}: {count} rows")

    # 4. Check if the SAME address appears multiple times (true duplicate) or DIFFERENT addresses
    print("\n" + "=" * 80)
    print("ADDRESS ANALYSIS for SBI ATM in Mandla (are they the same location?)")
    print("=" * 80)
    
    addr_check = conn.execute(text("""
        SELECT address, COUNT(*) as cnt 
        FROM raw_google_map_drive_data
        WHERE LOWER(name) LIKE 'sbi atm%' 
          AND city = 'Mandla'
          AND category = 'atm'
        GROUP BY address
        ORDER BY cnt DESC
    """)).fetchall()

    for r in addr_check:
        addr = (r[0] or "---")[:70]
        print(f"  [{r[1]}x] {addr}")
