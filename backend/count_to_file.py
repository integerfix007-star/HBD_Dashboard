"""Count exact duplicates where name + phone + city + address are ALL same - Result to file"""
from sqlalchemy import create_engine, text
import urllib.parse, os
from dotenv import load_dotenv

load_dotenv()
pw = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "darshit@1912"))
engine = create_engine(
    f"mysql+pymysql://{os.getenv('DB_USER')}:{pw}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT','3306')}/{os.getenv('DB_NAME')}?charset=utf8mb4"
)

tables = ["raw_google_map_drive_data", "raw_clean_google_map_data", "g_map_master_table"]
output = []

with engine.connect() as conn:
    conn.execute(text("SET SESSION sql_mode=''"))
    output.append("=" * 65)
    output.append("EXACT DUPLICATES (name + phone + city + address ALL same)")
    output.append("=" * 65)

    for table in tables:
        total = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
        groups = conn.execute(text(f"SELECT COUNT(*) FROM (SELECT 1 FROM {table} GROUP BY name, phone_number, city, address HAVING COUNT(*) > 1) t")).fetchone()[0]
        extra = conn.execute(text(f"SELECT COALESCE(SUM(cnt-1),0) FROM (SELECT COUNT(*) as cnt FROM {table} GROUP BY name, phone_number, city, address HAVING cnt > 1) t")).fetchone()[0]
        output.append(f"\n  {table}:")
        output.append(f"    Total rows:           {total:>10,}")
        output.append(f"    Duplicate groups:     {groups:>10,}")
        output.append(f"    Extra rows to remove: {extra:>10,}")

    output.append("\n" + "=" * 65)

with open("count_results.txt", "w") as f:
    f.write("\n".join(output))
