# 🚀 Honeybee Digital ETL Pipeline: Process Flow Guide

This document explains the high-speed, parallel background architecture of the Google Maps ETL system.

---

## 🏗️ 3-Layer Parallel Architecture

The system runs two independent, non-blocking threads alongside the Flask API. This ensures the dashboard stays live while data is processed at massive scale.

### 1. Ingestion Layer (`ScannerThread`)
**Purpose**: Monitors Google Drive and brings raw data into the local database.
- **Trigger**: Every 60 seconds (or reactive via GDrive Changes API).
- **Process**:
    - Scans 5,000+ folders for new or modified CSV files.
    - **Fingerprint Check**: Skips files that were already processed based on `drive_file_id`.
    - **Universal Normalizer**: Preserves 100% of Unicode text (Gujarati, Hindi, Tamil, etc.).
    - **Storage**: Inserts data into `raw_google_map_drive_data`.

### 2. Validation Layer (`ValidatorThread`)
**Purpose**: Batches raw records to check for quality, structure, and duplicates.
- **Trigger**: Continuous (processes in batches of 1,000 rows).
- **Process**:
    - **Step 1: Mandatory Check**: Ensures Name, Address, Phone, City, State, and Category are present.
    - **Step 2: Format Check**: Validates Phone (10-15 digits) and Website structure.
    - **Step 3: Duplicate Detection (Type 2)**: Checks for "Logical Signature" match (Phone + Lowercase Name + Lowercase Address).
    - **Storage**: Updates `validation_raw_google_map` with a status:
        - `MISSING`: Field is empty or null.
        - `INVALID`: Incorrect phone format.
        - `DUPLICATE`: logical match found in clean data.
        - `VALID`: Passed all checks.

### 3. Production Layer (Promotion)
**Purpose**: Provides "Golden Records" for the final dashboard.
- **Process**: Only rows marked as **VALID** and **NOT DUPLICATE** are promoted to `raw_clean_google_map_data`.
- **Audit Log**: Every batch of 1,000 saves a summary to `data_validation_log`.

---

## 📝 Example Flow

### Input Record (From CSV):
```json
{
  "name": "હનીબી ડિજિટલ (Honeybee Digital)",
  "phone_number": "+91 98765-43210",
  "address": "123 Main St, Surat",
  "website": "www.honeybee.com"
}
```

### 1. Ingestion Result (`raw_google_map_drive_data`):
- **Name**: `હનીબી ડિજિટલ (Honeybee Digital)` (Preserved exactly)
- **Phone**: `+91 98765-43210` (Original)
- **Status**: New row created with a unique `id`.

### 2. Validation Check:
- **Phone Normalized**: `919876543210` (Length 12 ✅)
- **Structure Check**: All mandatory fields found ✅
- **Duplicate Check**: Is there already a "honeybee digital" at "123 main st, surat" with phone "919876543210"? (❌ No)

### 3. Final Production Result (`raw_clean_google_map_data`):
- **Validation Status**: `VALID`
- **Cleaning**: Phone becomes `919876543210`, Website becomes `https://honeybee.com`.
- **Dashboard**: Row immediately appears in "Clean Production Data".

---

## 🛠️ Key Technical Features

- **Crash-Safe Resumption**: Uses `last_processed_id` in `etl_metadata`. If the server stops, it starts exactly where it left off.
- **Multilingual Safety**: No ASCII-only filters. Hindi, Tamil, Gujarati, etc., are treated as valid business data.
- **Logical Deduplication**: Even if the name has different spacing (e.g., "Honeybee" vs "Honey bee"), the logical normalization catches it if the phone and address match.
- **Audit Trail**: Every pipeline run is recorded in the `data_validation_log` table for performance monitoring.

---

## 🚀 How to Run
```powershell
cd backend
python app.py --runserver
```
*Note: Keep the terminal open; the threads run in the background of the Flask process.*
