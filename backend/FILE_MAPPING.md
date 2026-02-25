# Validation Core Logic - File Mapping Guide

This document provides a mapping of all files gathered in the `Validation_Core_Logic` folder to their respective destination paths in the main `backend` and `frontend` project directories.

## Backend Files (`backend/`)

| File Name | Destination Path | Description |
| :--- | :--- | :--- |
| `etl_pipeline.py` | `backend/etl_pipeline.py` | Main forward-flow ETL pipeline logic. |
| `normalizer.py` | `backend/model/normalizer.py` | Universal Unicode-safe data normalizer. |
| `validate_google_map_data.py` | `backend/validate_google_map_data.py` | Specialized Google Maps validation script. |
| `robust_gdrive_etl_v2.py` | `backend/model/robust_gdrive_etl_v2.py` | Google Drive ingestion logic. |
| `std_codes.json` | `backend/std_codes.json` | JSON data for Indian STD codes validation. |
| `honey-bee-digital-d96daf6e6faf.json` | `backend/model/honey-bee-digital-d96daf6e6faf.json` | Google Service Account credentials. |
| `.env` | `backend/.env` | Environment configuration file. |
| `init_db.py` | `backend/init_db.py` | Database initialization script. |
| `setup_local_db.py` | `backend/setup_local_db.py` | Local database setup utility. |
| `run_etl.py` | `backend/run_etl.py` | Entry point script to trigger the ETL process. |
| `sql/architect_schema.sql` | `backend/sql/architect_schema.sql` | SQL DDL for validation system tables. |
| `routes/gdrive_etl_routes/dashboard_stats.py` | `backend/routes/gdrive_etl_routes/dashboard_stats.py` | API routes for dashboard statistics. |
| `routes/gdrive_etl_routes/validation_dashboard.py` | `backend/routes/gdrive_etl_routes/validation_dashboard.py` | API routes for the validation dashboard. |
| `ETL_SYSTEM_DESIGN.md` | `backend/docs/ETL_SYSTEM_DESIGN.md` | Documentation for ETL system design. |
| `SYSTEM_INTEGRATION_GUIDE.md` | `backend/docs/SYSTEM_INTEGRATION_GUIDE.md` | Integration guide for the validation system. |

## Frontend Files (`frontend/`)

| File Name | Destination Path | Description |
| :--- | :--- | :--- |
| `frontend/componunts/masterdata/ValidationDashboard.jsx` | `frontend/src/componunts/masterdata/ValidationDashboard.jsx` | React component for the Validation Dashboard. |
| `frontend/componunts/masterdata/ValidationReport.jsx` | `frontend/src/componunts/masterdata/ValidationReport.jsx` | React component for Validation Reports. |

---

> [!NOTE]
> Ensure that all backend files are placed within the `backend/` directory and frontend files within `frontend/src/`. Some files may require additional dependencies (e.g., Python libraries or NPM packages) to function correctly.
