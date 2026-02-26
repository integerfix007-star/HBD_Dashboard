"""Show all 1604 exact duplicate groups from raw_google_map_drive_data"""
from sqlalchemy import create_engine, text
import urllib.parse, os
from dotenv import load_dotenv

load_dotenv()
pw = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "darshit@1912"))
engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','3306')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
)

lines = []
def log(msg=""):
    lines.append(msg)

with engine.connect() as conn:
    conn.execute(text("SET SESSION sql_mode=''"))

    dupes = conn.execute(text("""
        SELECT name, phone_number, city, LEFT(address,60) as addr, COUNT(*) as cnt,
               GROUP_CONCAT(id ORDER BY id SEPARATOR ',') as ids
        FROM raw_google_map_drive_data
        GROUP BY name, phone_number, city, address
        HAVING cnt > 1
        ORDER BY cnt DESC
    """)).fetchall()

    log(f"{'#':<6}{'Name':<40}{'Phone':<16}{'City':<20}{'Address (60 chars)':<62}{'Count':<6}{'IDs'}")
    log("-" * 180)

    for i, r in enumerate(dupes, 1):
        name = str(r[0] or "---")[:38]
        phone = str(r[1] or "---")[:14]
        city = str(r[2] or "---")[:18]
        addr = str(r[3] or "---")[:60]
        ids = str(r[5] or "")[:40]
        log(f"{i:<6}{name:<40}{phone:<16}{city:<20}{addr:<62}{r[4]:<6}{ids}")

    log(f"\nTotal duplicate groups: {len(dupes)}")
    log(f"Total extra rows: {sum(r[4]-1 for r in dupes)}")

with open("raw_duplicates_list.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Saved {len(dupes)} duplicate groups to raw_duplicates_list.txt")
print(f"\nFirst 30:")
for line in lines[:32]:
    print(line)
