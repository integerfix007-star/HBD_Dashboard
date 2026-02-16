from flask import Blueprint, jsonify, request
from sqlalchemy import text
from database.session import engine
import logging
import time

logger = logging.getLogger("DashboardAPI")
dashboard_bp = Blueprint("dashboard_v4", __name__)

TABLE = "raw_google_map_drive_data"

# Simple in-memory cache
CACHE = {
    "summary": None,
    "last_summary": 0
}
CACHE_TTL = 30 # 30 seconds

def execute_read(query, params=None):
    """Helper to execute read queries and return list of rows (materialized)."""
    with engine.connect() as conn:
        conn.execute(text("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED"))
        result = conn.execute(text(query), params or {})
        return result.fetchall()

@dashboard_bp.route("/api/model/stats", methods=["GET"])
def get_stats():
    state = request.args.get('state')
    cat = request.args.get('category')
    
    # If filtered, we still use live queries but they should be indexed
    if state or cat:
        where_clauses = []
        params = {}
        if state:
            where_clauses.append("state = :state")
            params['state'] = state
        if cat:
            where_clauses.append("category = :cat")
            params['cat'] = cat
        
        where_str = f"WHERE {' AND '.join(where_clauses)}"
        
        try:
            total_res = execute_read(f"SELECT COUNT(*) FROM {TABLE} {where_str}", params)
            total = total_res[0][0] if total_res else 0
            
            states = 1 if state else execute_read(f"SELECT COUNT(DISTINCT state) FROM {TABLE} {where_str}", params)[0][0]
            cats = 1 if cat else execute_read(f"SELECT COUNT(DISTINCT category) FROM {TABLE} {where_str}", params)[0][0]
            csvs = execute_read(f"SELECT COUNT(DISTINCT drive_file_id) FROM {TABLE} {where_str}", params)[0][0]
            
            return jsonify({
                "status": "success", 
                "total_records": total, 
                "total_states": states, 
                "total_categories": cats,
                "total_csvs": csvs
            })
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # GLOBAL STATS - Use Summary Table for 4-5s target (actually <1s)
    try:
        rows = execute_read("SELECT total_records, total_states, total_categories, total_csvs FROM dashboard_stats_summary_v5 LIMIT 1")
        if rows:
            total, states, cats, csvs = rows[0]
            return jsonify({
                "status": "success", 
                "total_records": total, 
                "total_states": states, 
                "total_categories": cats,
                "total_csvs": csvs,
                "cached": True
            })
    except Exception as e:
        logger.error(f"Summary Read Error: {e}")

    # Fallback to live (slow)
    try:
        rows = execute_read(f"SELECT COUNT(*), COUNT(DISTINCT state), COUNT(DISTINCT category), COUNT(DISTINCT drive_file_id) FROM {TABLE}")
        total, states, cats, csvs = rows[0]
        return jsonify({
            "status": "success", 
            "total_records": total, 
            "total_states": states, 
            "total_categories": cats,
            "total_csvs": csvs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@dashboard_bp.route("/api/model/recent", methods=["GET"])
def get_recent():
    try:
        rows = execute_read(f"SELECT id, name, city, state, category, added_time, drive_file_path FROM {TABLE} ORDER BY id DESC LIMIT 100")
        data = [{"id": r[0], "name": r[1], "city": r[2], "state": r[3], "category": r[4], "added_time": str(r[5]), "path": r[6]} for r in rows]
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@dashboard_bp.route("/api/model/all", methods=["GET"])
def get_all():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    state = request.args.get('state')
    cat = request.args.get('category')
    file_name = request.args.get('file_name')
    offset = (page - 1) * limit
    
    params = {"limit": limit, "offset": offset}
    where_clauses = []
    if state: where_clauses.append("state = :state"); params['state'] = state
    if cat: where_clauses.append("category = :cat"); params['cat'] = cat
    if file_name: where_clauses.append("drive_file_name = :file_name"); params['file_name'] = file_name
    where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    
    try:
        rows = execute_read(f"SELECT id, name, address, website, phone_number, reviews_count, reviews_average, category, subcategory, city, state, area, drive_file_name, drive_file_path FROM {TABLE} {where_str} ORDER BY id DESC LIMIT :limit OFFSET :offset", params)
        data = []
        for r in rows:
            data.append({
                "id": r[0], "name": r[1], "address": r[2], "website": r[3], "phone_number": r[4],
                "reviews_count": r[5], "reviews_average": float(r[6] or 0), "category": r[7],
                "subcategory": r[8], "city": r[9], "state": r[10], "area": r[11], "drive_file_name": r[12],
                "drive_file_path": r[13]
            })
        return jsonify({"status": "success", "data": data, "page": page, "limit": limit})
    except Exception as e:
        logger.error(f"All Data Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@dashboard_bp.route("/api/model/files", methods=["GET"])
def get_files():
    state = request.args.get('state')
    cat = request.args.get('category')
    if not state or not cat: return jsonify({"status": "error", "message": "Required params missing"}), 400
    try:
        rows = execute_read(f"SELECT drive_file_name, COUNT(*), MAX(drive_uploaded_time), drive_file_path FROM {TABLE} WHERE state = :state AND category = :cat GROUP BY drive_file_name, drive_file_path", {"state": state, "cat": cat})
        data = [{"file_name": r[0], "count": r[1], "last_mod": str(r[2]), "path": r[3]} for r in rows]
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@dashboard_bp.route("/api/model/state-summary", methods=["GET"])
def get_state_summary():
    # Use Summary Table for Instant Category Explorer
    try:
        rows = execute_read("SELECT state, category, record_count FROM state_category_summary_v5")
        summary = {}
        for r in rows:
            st = r[0] or "Unknown"
            if st not in summary: summary[st] = {"state": st, "total": 0, "categories": {}}
            summary[st]["total"] += r[2]
            summary[st]["categories"][r[1] or "General"] = r[2]
        return jsonify({"status": "success", "data": summary})
    except Exception as e:
        logger.error(f"State Summary Read Error: {e}")

    # Fallback
    try:
        rows = execute_read(f"SELECT state, category, COUNT(*) FROM {TABLE} GROUP BY state, category")
        summary = {}
        for r in rows:
            st = r[0] or "Unknown"
            if st not in summary: summary[st] = {"state": st, "total": 0, "categories": {}}
            summary[st]["total"] += r[2]
            summary[st]["categories"][r[1] or "General"] = r[2]
        return jsonify({"status": "success", "data": summary})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@dashboard_bp.route("/api/model/folder-status", methods=["GET"])
def get_folder_status():
    """Returns the status of all scanned folders from the registry."""
    try:
        rows = execute_read("SELECT folder_name, csv_count, scanned_at, status FROM drive_folder_registry ORDER BY scanned_at DESC")
        data = [
            {
                "folder_name": r[0],
                "csv_count": r[1],
                "last_scanned": str(r[2]),
                "status": r[3]
            } for r in rows
        ]
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        logger.error(f"Folder Status Error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
