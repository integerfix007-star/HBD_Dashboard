import os
import json
from pathlib import Path
from flask import Blueprint, jsonify, request, make_response
from sqlalchemy import func, or_, text
from werkzeug.utils import secure_filename
from datetime import datetime
import hashlib

# Model and Session imports
from model.master_table_model import MasterTable
from model.upload_master_reports_model import UploadReport
from database.session import get_db_session
from extensions import redis_client

# --- INITIALIZE BLUEPRINT FIRST ---
master_table_bp = Blueprint("master_table", __name__)

# Define upload directory helper
def get_upload_base_dir():
    return Path(os.getenv("UPLOAD_DIR", "./uploads"))

# Import Celery task safely
try:
    from tasks.upload_master_task import process_master_upload_task
except ImportError:
    process_master_upload_task = None

# Cache constants
CACHE_TTL = 300  # 5 minutes

def _get_cache_key(task_id=None):
    """Generate cache key based on task_id"""
    return f"dashboard_stats_{task_id or 'all'}"

def _get_cached_data(cache_key):
    """Get data from Redis cache"""
    if not redis_client:
        return None
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"⚠ Redis get error: {e}")
    return None

def _set_cached_data(cache_key, data, etag):
    """Store data in Redis cache with TTL"""
    if not redis_client:
        return
    try:
        cache_data = {
            "data": data,
            "etag": etag,
            "cached_at": datetime.utcnow().isoformat()
        }
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(cache_data))
    except Exception as e:
        print(f"⚠ Redis set error: {e}")

def _set_cache_headers(response, etag):
    """Set proper HTTP caching headers"""
    response.headers['Cache-Control'] = f'public, max-age={CACHE_TTL}'
    response.headers['ETag'] = etag
    response.headers['X-Cache-Source'] = 'Redis' if redis_client else 'Memory'
    return response

# --- ROUTES ---

@master_table_bp.route("/upload/master", methods=["POST"])
def upload_master():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    UPLOAD_DIR = get_upload_base_dir() / "master"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        path = UPLOAD_DIR / filename
        f.save(path)
        paths.append(str(path))

    if process_master_upload_task:
        task = process_master_upload_task.delay(paths)
        return jsonify({
            "status": "files_accepted",
            "task_id": task.id
        }), 202
    return jsonify({"error": "Upload task not configured"}), 500

@master_table_bp.route("/master_table/list", methods=["GET"])
def get_master_table_list():
    session = get_db_session()
    try:
        page = request.args.get("page", 1, type=int)
        # Default to 10 for resource safety
        limit = request.args.get("limit", 10, type=int)
        search = request.args.get("search", "", type=str)

        # Hard cap to prevent frontend from accidentally crashing the DB
        limit = max(1, min(limit, 50))

        query = session.query(MasterTable)

        if search:
            query = query.filter(
                or_(
                    MasterTable.business_name.ilike(f"%{search}%"),
                    MasterTable.city.ilike(f"%{search}%"),
                    MasterTable.business_category.ilike(f"%{search}%"),
                    MasterTable.global_business_id.ilike(f"%{search}%")
                )
            )

        total_count = query.count()
        total_pages = (total_count + limit - 1) // limit

        rows = query.order_by(MasterTable.id.desc()).offset((page - 1) * limit).limit(limit).all()

        return jsonify({
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "data": [row.to_dict() for row in rows]
        })
    except Exception as e:
        print(f"❌ Error fetching master list: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@master_table_bp.route("/master-dashboard-stats", methods=["GET"])
def get_master_dashboard_stats():
    task_id = request.args.get('task_id')
    cache_key = _get_cache_key(task_id)
    
    # Check if-none-match header for client-side caching
    if_none_match = request.headers.get('If-None-Match')
    
    # Check Redis cache first
    cached_entry = _get_cached_data(cache_key)
    if cached_entry:
        cached_data = cached_entry.get("data")
        cached_etag = cached_entry.get("etag")
        
        if if_none_match == cached_etag:
            return make_response('', 304)  # Not Modified
        
        result = {
            "status": "COMPLETED",
            "stats": cached_data,
            "source": "Redis Cache"
        }
        response = make_response(jsonify(result))
        return _set_cache_headers(response, cached_etag)
    
    session = get_db_session()
    where_clause = "WHERE 1=1"
    params = {}
    if task_id:
        where_clause += " AND task_id = :task_id"
        params['task_id'] = task_id

    try:
        # Optimization 1: Combined meta + phone distribution in one query
        meta_query = text(f"""
            SELECT 
                COUNT(*) as total,
                ROUND(AVG(ratings), 1) as avg_r,
                SUM(CASE WHEN COALESCE(primary_phone, secondary_phone, other_phones, virtual_phone, whatsapp_phone, '') != '' THEN 1 ELSE 0 END) as has_phone
            FROM master_table {where_clause}
        """)
        meta_res = session.execute(meta_query, params).fetchone()
        total_records = meta_res.total or 0
        avg_rating = float(meta_res.avg_r or 0.0)
        has_phone = meta_res.has_phone or 0
        missing_phone = total_records - has_phone

        # Optimization 2: Separate queries for different stats
        state_query = text(f"SELECT state, COUNT(*) as count FROM master_table {where_clause} AND state != '' GROUP BY state ORDER BY count DESC LIMIT 5")
        states = [dict(row._mapping) for row in session.execute(state_query, params)]

        city_query = text(f"SELECT city as name, COUNT(*) as count FROM master_table {where_clause} AND city != '' GROUP BY city ORDER BY count DESC LIMIT 5")
        top_cities = [dict(row._mapping) for row in session.execute(city_query, params)]
        
        sub_query = text(f"SELECT business_category as name, COUNT(*) as count FROM master_table {where_clause} GROUP BY business_category ORDER BY count DESC LIMIT 5")
        top_subs = [dict(row._mapping) for row in session.execute(sub_query, params)]

        top_rated_query = text(f"""
            SELECT business_name as name, city, ratings as stars
            FROM master_table {where_clause} 
            AND ratings >= 4.0 
            ORDER BY ratings DESC LIMIT 5
        """)
        top_rated = [dict(row._mapping) for row in session.execute(top_rated_query, params)]

        stats_data = {
            "total_records": total_records,
            "avg_system_rating": avg_rating,
            "state_summary": states,
            "phone_distribution": [
                {"name": "With Contact No.", "value": int(has_phone), "fill": "#10b981"},
                {"name": "No Contact No.", "value": int(missing_phone), "fill": "#ef4444"}
            ],
            "top_cities": top_cities,
            "top_subcategories": top_subs,
            "top_rated_businesses": top_rated,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        # Generate ETag
        stats_json = str(stats_data).encode()
        etag = hashlib.md5(stats_json).hexdigest()
        
        # Store in Redis cache
        _set_cached_data(cache_key, stats_data, etag)
        
        result = {
            "status": "COMPLETED",
            "stats": stats_data,
            "source": "Database Query"
        }
        
        response = make_response(jsonify(result))
        return _set_cache_headers(response, etag)
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500
    finally:
        session.close()
@master_table_bp.route("/upload/report/<task_id>", methods=["GET"])
def get_upload_report(task_id):
    session = get_db_session()
    try:
        report = session.query(UploadReport).filter_by(task_id=task_id).first()
        if not report:
            return jsonify({"status": "not_found", "task_id": task_id}), 404

        return jsonify({
            "task_id": report.task_id,
            "status": report.status,
            "stats": {
                "total_records": report.total_processed or 0,
                "missing_values": {
                    "missing_phone": report.missing_primary_phone or 0,
                    "missing_email": report.missing_email or 0,
                    "missing_address": report.missing_address or 0
                }
            }
        })
    finally:
        session.close()