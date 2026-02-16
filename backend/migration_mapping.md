# 🗺️ Migration Mapping & Path Changes

This document summarizes the restructuring of the Google Drive Automation system. All core logic has been moved from the `scripts` directory to the `model` package for better integration and modularity.

## 📁 File System Changes

| Original Path (Deleted/Moved) | New Path (Current) |
| :--- | :--- |
| `backend/scripts/gdrive_etl/robust_gdrive_etl_v2.py` | `backend/model/robust_gdrive_etl_v2.py` |
| `backend/scripts/gdrive_etl/ingestion_service.py` | `backend/model/ingestion_service.py` |
| `backend/scripts/gdrive_etl/ingestion_newest_only.py` | `backend/model/ingestion_newest_only.py` |
| `backend/scripts/gdrive_etl/normalizer.py` | `backend/model/normalizer.py` |
| `backend/scripts/gdrive_etl/honey-bee-digital-*.json` | `backend/model/honey-bee-digital-*.json` |

## 🌐 API Route Changes

The API prefix has been updated to reflect the move to the model-driven architecture.

| Old Endpoint | New Endpoint |
| :--- | :--- |
| `/api/dashboard/stats` | `/api/model/stats` |
| `/api/dashboard/recent` | `/api/model/recent` |
| `/api/dashboard/all` | `/api/model/all` |
| `/api/dashboard/files` | `/api/model/files` |
| `/api/dashboard/state-summary` | `/api/model/state-summary` |
| `/api/dashboard/folder-status` | `/api/model/folder-status` |

## 🗑️ Cleaned Up (Deleted) Files
The following temporary utilities and log files were removed to maintain a clean workspace:
- `backend/find_srinagar.py`
- `backend/count_sachin.py`
- `backend/estimate_etl.py`
- `backend/etl_log.txt`
- `backend/diag_output.txt`
- `backend/proc_list.txt`
- `backend/input.txt`
- `backend/scripts/gdrive_etl/` (Entire directory removed after migration)

## 🛠️ Code References Updated
- **Backend**: `backend/app.py` updated to use `from model.robust_gdrive_etl_v2 import ...`.
- **Backend API**: `backend/routes/gdrive_etl_routes/dashboard_stats.py` updated with new route prefixes.
- **Frontend**: `frontend/src/componunts/masterdata/RawCleanedData.jsx` updated to fetch from `/api/model/` endpoints.
