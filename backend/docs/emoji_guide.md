# HBD Dashboard Emoji Guide 🧭

This document explains the meaning of the emojis used in the backend logs and the frontend dashboard UI.

## 📊 Dashboard UI (Frontend)
These icons appear in the **GDrive ETL Explorer** on the dashboard.

| Emoji | Label | Location | Meaning |
| :--- | :--- | :--- | :--- |
| **🚀** | **LIVE** | City / File | Appears on cities or files that were added or modified **today**. |
| **✨** | **Newly Scanned** | Source | Indicates the folder/category was discovered in the current scan session. |
| **📀** | **From Database** | Source | Data was already stored in the database from a previous session. |
| **📂** | **New Folder** | Category | A newly discovered folder structure. |
| **🗄️** | **Existing Folder**| Category | A previously known folder. |
| **✅** | **Synced** | File Status | The file has been successfully processed and stored. |
| **🆕** | **New** | Name | Appended to city or category names when new activity is detected. |

---

## 🛠️ ETL Sync Status (Backend)
These emojis appear in the console logs during background synchronization.

| Emoji | Meaning | Description |
| :--- | :--- | :--- |
| **📄** | **NEW** | A brand new file was discovered on Google Drive. |
| **🔄** | **UPDATED** | An existing file's metadata was refreshed or fixed. |
| **�** | **DEEP SCAN** | Multi-threaded workers are diving into sub-folders. |
| **✅** | **SUCCESS** | A folder or file was successfully scanned. |
| **❌** | **FAILED** | A critical error occurred while reading a file. |
| **⚠️** | **WARNING** | A minor issue occurred (e.g., folder metadata fetch failed). |
| **🚀** | **START SCAN** | Initializing a full recursive scan of Google Drive. |

---

## 📂 Code References
- **Frontend UI**: `frontend/src/componunts/masterdata/RawCleanedData.jsx`
- **Backend ETL**: `backend/scripts/gdrive_etl/robust_gdrive_etl.py`
- **Secondary ETL**: `backend/scripts/gdrive_etl/ingestion_newest_only.py`

---
*Last Updated: 2026-02-03*
