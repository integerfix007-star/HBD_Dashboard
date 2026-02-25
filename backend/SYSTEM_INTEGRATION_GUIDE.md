# Google Maps ETL: System Integration & Data Flow Guide

This guide explains how the high-throughput ETL system works, how to integrate it with the HBD Dashboard, and provides visual examples of data transformation across the three-tier architecture.

---

## 🏗️ 1. The Three-Tier Architecture

Data moves in one direction: **Forward**. No deletions, no updates to raw data.

1.  **`raw_google_map_drive_data`**: The Ingestion Layer (Read-Only).
2.  **`validation_raw_google_map`**: The Processing & Validation Controller.
3.  **`raw_clean_google_map_data`**: The Production-Ready Data Store.

---

## 🔄 2. Complete Data Flow

### Step A: Ingestion (Sync)
New rows from the raw table are snapshotted into the validation table.
*   **Trigger**: Every 30 seconds or manually.
*   **Logic**: `INSERT ... SELECT ... LEFT JOIN ... WHERE validation.raw_id IS NULL`.

### Step B: Validation (The Filter)
Worker picks rows where `validation_status = 'PENDING'`.
*   **Checks**: Mandatory fields, phone/URL formats, and cross-table duplicate detection.
*   **Outcome**: Status changes to `STRUCTURED` (Success), `INVALID`, `UNSTRUCTURED`, or `DUPLICATE`.

### Step C: Cleaning (The Polish)
Worker picks rows where `status = 'STRUCTURED'` and `cleaning_status = 'NOT_STARTED'`.
*   **Logic**: Trims whitespace, normalizes phone numbers, forces HTTPS.
*   **Action**: Inserts final record into `raw_clean_google_map_data` and marks validation table as `CLEANED`.

---

## 📊 3. Table Row Examples (End-to-End Migration)

### Tier 1: Raw Data (Dirty)
| id | name | phone_number | city | category |
| :--- | :--- | :--- | :--- | :--- |
| 101 | **"  Coffee Shop "** | `(011) 234-5678` | | Cafe |

### Tier 2: Validation Snapshot (Fail Case)
*Logic: Missing 'city'.*
| id | raw_id | validation_status | missing_fields |
| :--- | :--- | :--- | :--- |
| 5001 | 101 | **`UNSTRUCTURED`** | `"city"` |

### Tier 3: Clean Data (Success Case)
*After fixing raw and re-processing.*
| id | name | phone_number | city | category |
| :--- | :--- | :--- | :--- | :--- |
| 900 | **"Coffee Shop"** | `0112345678` | "Delhi" | "Cafe" |

---

## 💻 4. Dashboard Integration Guide

### A. Real-time Status Dashboard
To show the health of the ETL pipeline on the frontend, use these aggregation queries.

**Validation Funnel Query:**
```sql
SELECT validation_status, COUNT(*) as count
FROM validation_raw_google_map
GROUP BY validation_status;
```
*   *UI Use*: Display a pie chart or cards showing how many records are "Invalid" vs "Structured".

**Cleaning Progress Query:**
```sql
SELECT cleaning_status, COUNT(*) as count
FROM validation_raw_google_map
GROUP BY cleaning_status;
```

### B. "Fix Required" View
Create a dashboard tab that pulls rows where `validation_status IN ('INVALID', 'UNSTRUCTURED')`.
*   **Query**: `SELECT id, name, missing_fields, validation_errors FROM validation_raw_google_map WHERE validation_status = 'INVALID';`
*   **UI Idea**: Show a table where the user can see what's wrong with specific records and fix them at the source.

### C. Search & Production Data
The frontend search and "Final Reports" should **ONLY** query the clean table.
*   **Query**: `SELECT * FROM raw_clean_google_map_data WHERE city = 'Srinagar' LIMIT 50;`

---

## 🚀 5. Integration Checklist
1.  [ ] **Run DDL**: Execute `sql/architect_schema.sql` on the production database.
2.  [ ] **Deploy Worker**: Run `scripts-validation-validate_google_map_data.py.py` as a background service or call its `run_full_pipeline()` in your app loop.
3.  [ ] **Update Backend API**: Update your `/get-data` endpoints to read from `raw_clean_google_map_data` instead of the raw table for production views.
4.  [ ] **Add Admin Charts**: Add the status counts to the Dashboard sidebar.

---

## 🛡️ 6. Performance Guarantees
- **Scalable**: Batch processing allows handling 100k+ rows without UI lag.
- **Safe**: No `DELETE` operations mean zero data loss risk.
- **Locked**: Using `raw_id UNIQUE` constraints prevents data duplication across all layers.
