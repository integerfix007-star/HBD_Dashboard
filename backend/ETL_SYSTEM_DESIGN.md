# High-Throughput Google Maps ETL System Design

## 1. MySQL DDL & Index Strategy

The DDL maintains strict data integrity and high performance for batch processing.

```sql
-- See sql/architect_schema.sql for the full DDL.
-- Key highlights:
-- - Unique constraint on raw_id prevents row duplication.
-- - Composite indexes on (name, address, phone_number) enable sub-millisecond deduplication.
-- - Status enums are indexed for efficient batch selection.
```

---

## 2. Step-by-Step Logic

### Phase 1: Raw → Validation (Ingestion)
**Purpose:** Create a snapshot of raw data for processing without touching the original table.

```sql
INSERT INTO validation_raw_google_map (
    raw_id, name, address, website, phone_number, reviews_count, reviews_avg, 
    category, subcategory, city, state, area, created_at
)
SELECT 
    r.id, r.name, r.address, r.website, r.phone_number, r.reviews_count, r.reviews_avg, 
    r.category, r.subcategory, r.city, r.state, r.area, r.created_at
FROM raw_google_map_drive_data r
LEFT JOIN validation_raw_google_map v ON r.id = v.raw_id
WHERE v.raw_id IS NULL;
```

---

### Phase 2: Validation Engine (Worker Logic)
**Batch Size:** 1,000 records
**Query:** `SELECT * FROM validation_raw_google_map WHERE validation_status = 'PENDING' LIMIT 1000;`

#### Step 1: Mandatory Field Check
```python
def check_mandatory(row):
    required = ["name", "address", "category", "city", "state", "phone_number"]
    missing = [f for f in required if not row[f] or str(row[f]).strip() == "" or is_placeholder(row[f])]
    if missing:
        return "UNSTRUCTURED", ",".join(missing)
    return "PENDING", None
```

#### Step 2: Format Validation
```python
def validate_formats(row):
    errors = []
    
    # Phone: 10-15 digits only
    phone = re.sub(r'\D', '', str(row['phone_number']))
    if not (10 <= len(phone) <= 15):
        errors.append("phone_format")
        
    # Website: Strict https
    website = str(row['website']).lower().strip()
    if website and not website.startswith('https://'):
        errors.append("website_protocol")
        
    # Numeric checks
    if not (0 <= row['reviews_avg'] <= 5):
        errors.append("reviews_avg_range")
        
    if errors:
        return "INVALID", ",".join(errors)
    return "PENDING", None
```

#### Step 3: Duplicate Detection (Strict)
**SQL Logic:**
```sql
SELECT c.id 
FROM raw_clean_google_map_data c
WHERE 
    LOWER(REPLACE(c.name, ' ', '')) = LOWER(REPLACE(?, ' ', ''))
    AND LOWER(REPLACE(c.address, ' ', '')) = LOWER(REPLACE(?, ' ', ''))
    AND REPLACE(REPLACE(REPLACE(c.phone_number, '-', ''), ' ', ''), '+', '') = ?;
```

---

### Phase 3: Cleaning Engine
**Query:** `SELECT * FROM validation_raw_google_map WHERE validation_status = 'STRUCTURED' AND cleaning_status = 'NOT_STARTED' LIMIT 5000;`

**Logic:**
1.  **Normalize Phone:** Remove all non-digits.
2.  **Clean Website:** Prepend `https://` if missing, lowercase all.
3.  **Trim Strings:** `strip()` all text fields.
4.  **Bulk Insert:** Insert into `raw_clean_google_map_data`.
5.  **State Update:** `UPDATE validation_raw_google_map SET cleaning_status = 'CLEANED' WHERE id IN (...)`

---

## 3. Performance & Reliability

### Safe Batch Processing
- **Transactions:** Each batch of 5000 is wrapped in a single transaction.
- **Concurrency:** Uses `FOR UPDATE SKIP LOCKED` (if MySQL 8.0+) or optimized batch IDs to allow multiple workers without collision.
- **No Raw Locking:** The `LEFT JOIN` on ingestion is a read-only operation on `raw_google_map_drive_data`.

### Scalability
- **Partitioning:** If `raw_clean_google_map_data` grows beyond 50M rows, partition by `city` or `created_at`.
- **Worker Scaling:** Design is stateless; simply spin up more instances of the Validation/Cleaning workers.

### Crash Recovery
- Since state is tracked via `validation_status` and `cleaning_status`, interrupted jobs automatically resume on next run.

---

## 4. Dashboard Summary Queries

### Validation Breakdown
```sql
SELECT validation_status, COUNT(*) as volume
FROM validation_raw_google_map
GROUP BY validation_status;
```

### Cleaning Progress
```sql
SELECT cleaning_status, COUNT(*) as volume
FROM validation_raw_google_map
GROUP BY cleaning_status;
```
