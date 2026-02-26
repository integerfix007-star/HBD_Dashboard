"""
🔍 DUPLICATE ANALYSIS — Shows businesses appearing in MULTIPLE cities
   This helps understand WHY duplicates exist and what pattern to fix
"""
from sqlalchemy import create_engine, text
import urllib.parse, os
from dotenv import load_dotenv

load_dotenv()
pw = urllib.parse.quote_plus(os.getenv("DB_PASSWORD", "darshit@1912"))
user = os.getenv("DB_USER", "local_dashboard")
host = os.getenv("DB_HOST", "127.0.0.1")
db = os.getenv("DB_NAME", "local_dashboard")
port = os.getenv("DB_PORT", "3306")

engine = create_engine(
    f"mysql+pymysql://{user}:{pw}@{host}:{port}/{db}?charset=utf8mb4",
    connect_args={"read_timeout": 120, "write_timeout": 120}
)

lines = []
def log(msg=""):
    lines.append(msg)
    print(msg)

SEP = "=" * 120

with engine.connect() as conn:
    conn.execute(text("SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))
    conn.execute(text("SET SESSION sql_mode=''"))

    # ──────────────────────────────────────────────────────────────
    # ANALYSIS 1: Same name+phone appearing in DIFFERENT cities
    #   → These are REAL businesses in different locations (NOT duplicates)
    # ──────────────────────────────────────────────────────────────
    log(SEP)
    log("ANALYSIS 1: Same Name + Phone → DIFFERENT Cities (in g_map_master_table)")
    log("These are the SAME business chain in multiple cities — should they be separate rows?")
    log(SEP)

    multi_city = conn.execute(text("""
        SELECT name, phone_number, 
               GROUP_CONCAT(DISTINCT city ORDER BY city SEPARATOR ' | ') as cities,
               GROUP_CONCAT(DISTINCT category ORDER BY category SEPARATOR ' | ') as categories,
               COUNT(*) as total_rows,
               COUNT(DISTINCT city) as city_count
        FROM g_map_master_table
        WHERE name IS NOT NULL AND phone_number IS NOT NULL AND phone_number != ''
        GROUP BY name, phone_number
        HAVING COUNT(DISTINCT city) > 1
        ORDER BY city_count DESC, total_rows DESC
        LIMIT 30
    """)).fetchall()

    log(f"\nFound {len(multi_city)} businesses appearing in MULTIPLE cities:\n")
    for i, r in enumerate(multi_city, 1):
        log(f"  [{i}] {r[0]}")
        log(f"      Phone:      {r[1]}")
        log(f"      Cities:     {r[2]}")
        log(f"      Categories: {r[3]}")
        log(f"      Total Rows: {r[4]}  |  Distinct Cities: {r[5]}")
        log("")

    # ──────────────────────────────────────────────────────────────
    # ANALYSIS 2: EXACT duplicates — Same name+phone+city+category
    #   → These are TRUE duplicates that should be removed
    # ──────────────────────────────────────────────────────────────
    log(SEP)
    log("ANALYSIS 2: EXACT Duplicates — Same Name + Phone + City + Category (TRUE duplicates)")
    log("These should NOT exist — they are the same record inserted multiple times")
    log(SEP)

    exact_dupes = conn.execute(text("""
        SELECT name, phone_number, city, category, COUNT(*) as cnt
        FROM g_map_master_table
        WHERE name IS NOT NULL
        GROUP BY name, phone_number, city, category
        HAVING cnt > 1
        ORDER BY cnt DESC
        LIMIT 30
    """)).fetchall()

    exact_total = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT 1 FROM g_map_master_table
            GROUP BY name, phone_number, city, category
            HAVING COUNT(*) > 1
        ) t
    """)).fetchone()[0]

    extra_rows = conn.execute(text("""
        SELECT COALESCE(SUM(cnt - 1), 0) FROM (
            SELECT COUNT(*) as cnt FROM g_map_master_table
            GROUP BY name, phone_number, city, category
            HAVING cnt > 1
        ) t
    """)).fetchone()[0]

    log(f"\nTotal duplicate GROUPS: {exact_total}")
    log(f"Total extra ROWS to remove: {extra_rows}\n")

    if exact_dupes:
        for i, r in enumerate(exact_dupes, 1):
            log(f"  [{i}] {r[0]}")
            log(f"      Phone: {r[1]}  |  City: {r[2]}  |  Category: {r[3]}  |  Count: {r[4]}")
            log("")
    else:
        log("  ✅ No exact duplicates found!")

    # ──────────────────────────────────────────────────────────────
    # ANALYSIS 3: Show a specific example in detail
    # ──────────────────────────────────────────────────────────────
    if multi_city:
        example_name = multi_city[0][0]
        example_phone = multi_city[0][1]
        
        log(SEP)
        log(f"DEEP DIVE: All rows for '{example_name}' (phone: {example_phone})")
        log(SEP)

        detail = conn.execute(text("""
            SELECT id, name, phone_number, city, state, category, address
            FROM g_map_master_table
            WHERE name = :name AND phone_number = :phone
            ORDER BY city, id
        """), {"name": example_name, "phone": example_phone}).fetchall()

        log(f"\n  Found {len(detail)} rows:\n")
        log(f"  {'ID':<10}{'City':<22}{'State':<18}{'Category':<28}{'Address (first 50 chars)'}")
        log(f"  {'-'*110}")
        for r in detail:
            addr = str(r[6] or "---")[:50]
            log(f"  {r[0]:<10}{str(r[3] or '---'):<22}{str(r[4] or '---'):<18}{str(r[5] or '---'):<28}{addr}")

    # ──────────────────────────────────────────────────────────────
    # SUMMARY
    # ──────────────────────────────────────────────────────────────
    log(f"\n\n{SEP}")
    log("SUMMARY")
    log(SEP)
    
    total_master = conn.execute(text("SELECT COUNT(*) FROM g_map_master_table")).fetchone()[0]
    total_clean = conn.execute(text("SELECT COUNT(*) FROM raw_clean_google_map_data")).fetchone()[0]
    
    log(f"  Master Table Total:          {total_master:>10,}")
    log(f"  Clean Table Total:           {total_clean:>10,}")
    log(f"  Multi-city businesses:       {len(multi_city):>10}")
    log(f"  Exact duplicate groups:      {exact_total:>10}")
    log(f"  Extra rows (true dupes):     {extra_rows:>10}")
    log("")
    log("  CONCLUSION:")
    if len(multi_city) > 0:
        log("  → Businesses with SAME name+phone in DIFFERENT cities = REAL separate locations (KEEP them)")
    if exact_total > 0:
        log(f"  → {exact_total} groups have EXACT same name+phone+city+category = TRUE duplicates (REMOVE them)")
    else:
        log("  → No exact duplicates found — the data is clean!")

with open("duplicate_report.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"\n>>> Full report saved to: duplicate_report.txt")
