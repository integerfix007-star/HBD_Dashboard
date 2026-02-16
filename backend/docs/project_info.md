# 📊 Project Documentation & Emoji Guide

This document explains the logic behind the Google Drive automation and the visual feedback system used in the HBD Dashboard.

---

## 🏛️ Data Organization Logic

### 🌍 The "General" Category
You may see files or folders assigned to the `General` category. This happens in the following cases:
- **Root Level Files**: Files found directly in the "Google Map Data" folder without a sub-folder.
- **Ambiguous Names**: If a folder name is generic (like "Data", "Export", or "New") and the filename doesn't contain a clear city/category, the system defaults to `General` to ensure the data is preserved rather than discarded.
- **Top Level Folders**: Direct children of the root that don't match the specific "City/Category" hierarchy yet.

### 📂 Empty Folders
The dashboard shows folders even if they have **0 Files**.
- **Why?**: The system scans the entire Drive structure first. If it finds a folder (e.g., "Krunali") it records it immediately so you know it's being watched.
- **Why are they empty?**: 
  - The folder might contain non-CSV files (which the ETL ignores).
  - The folder might be a "container" for other sub-folders.
  - The scan is still in progress and hasn't reached the files inside yet.

---

## 🎨 Emoji Guide (Terminal & Logs)

### 📁 Folders & Scanning
- `🚀 [SCAN START]`: The ETL has initiated a fresh pass of your Google Drive.
- `📂 Folder: [Name]`: The scanner is currently moving into this directory.
- `🏁 [DEEP SCAN]`: Multi-threaded workers are diving deep into sub-folders.

### 📄 File Ingestion
- `NEW 📄`: A brand new CSV was found and added to the database for the first time.
- `UPDATED 🔄`: The file was already in the database, but it was verified or refreshed.
- `🆕 Synced`: High-speed confirmation that data is now live.
- `✅ [TODAY 🚀]`: This file was modified on Google Drive **today**! It gets priority.

### ⚠️ Errors
- `❌ Failed`: There was a problem reading a specific file (usually a corrupted CSV).
- `⚠️ Error scanning`: A network or SSL glitch occurred; the system will auto-retry.

---

## 📖 Dashboard View Guide

The dashboard is divided into two primary views to help you track both progress and data details.

### 1. 📊 Overview Stats (Inventory)
This is the default view where you see the high-level summary.
- **City & Category**: Shows you where the data came from.
- **Inventory Count**: The total number of CSV records already ingested for that specific city/category.
- **Live 🚀 Badge**: Appears on any city that has had folder activity or new file discovery **today**. This tells you the automation is currently active in that region.
- **Source Column**: 
  - `✨ Newly Scanned`: The scanner found this folder/category during the current background session.
  - `📀 From Database`: This data was already stored and is being verified for updates.

### 2. 🔍 Itemized Files (Detail View)
Clicking on a row in the stats table opens the detail view for that specific category.
- **🚀 Icon**: Indicates a file that was ingested or modified **today**. 
- **✅ Icon**: Indicates a file that is already successfully synced and stored from previous days.
- **Drive Path**: Shows the exact location in Google Drive where the file lives.

---

## 🖥️ Indicator Cheat Sheet

| Icon | Location | Meaning |
| :--- | :--- | :--- |
| `LIVE 🚀` | City Column | New activity detected in this city **today**. |
| `✨ Newly Scanned` | Source Column | Found in the current scan session. |
| `📀 From Database`| Source Column | Historical data already in permanent storage. |
| `📂` | Category | A newly discovered folder structure. |
| `🗄️` | Category | A previously known folder. |
| `🚀` | File Name | File added or modified **today**. |
| `✅` | File Name | File already successfully synced. |

---

## 🕒 Background Sync
The system runs in the background every **10 minutes**. It uses **5 Parallel Workers** to ensure that even with 200+ categories, your data stays fresh without slowing down the server.
