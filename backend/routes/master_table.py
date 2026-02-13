from flask import Blueprint, jsonify, request
import redis
import os
from sqlalchemy import func, or_, text
from model.master_table_model import MasterTable
from database.session import get_db_session
from utils.storage import get_upload_base_dir
from werkzeug.utils import secure_filename
from tasks.upload_master_task import process_master_upload_task
from model.upload_master_reports_model import UploadReport


# Setup Redis connection (Docker Compose: use 'redis' hostname)
# Prefer REDIS_URL, fallback to CELERY_BROKER_URL, then default
REDIS_URL = os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "redis://redis:6379/0"
try:
    redis_client = redis.Redis.from_url(REDIS_URL)
    redis_client.ping()
except Exception:
    redis_client = None


master_table_bp = Blueprint("master_table", __name__)

@master_table_bp.route("/upload/master", methods=["POST"])
def upload_master():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    UPLOAD_DIR = get_upload_base_dir()/"master"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        path = UPLOAD_DIR/filename
        f.save(path)
        paths.append(str(path))

    task = process_master_upload_task.delay(paths)

    return jsonify({
        "status": "files_accepted",
        "task_id": task.id
    }), 202

@master_table_bp.route("/upload/report/<task_id>", methods=["GET"])
def get_upload_report(task_id):
    session = get_db_session()
    try:
        report = session.query(UploadReport).filter_by(task_id=task_id).first()

        if not report:
            return jsonify({
                "status": "not_found",
                "task_id": task_id
            }), 404

        base_stats = {
            "total_records": report.total_processed or 0,
            "total_cities": report.total_cities or 0,
            "total_areas": report.total_areas or 0,
            "total_categories": report.total_categories or 0,
            "city_match_status": (report.stats or {}).get(
                "city_match_status",
                {"matched": 0, "unmatched": 0}
            ),
            "missing_values": {
                "missing_phone": report.missing_primary_phone or 0,
                "missing_email": report.missing_email or 0,
                "missing_address": report.missing_address or 0
            }
        }

        return jsonify({
            "task_id": report.task_id,
            "status": report.status,
            "stats": base_stats
        })

    finally:
        session.close()

@master_table_bp.route("/api/master-dashboard-stats", methods=["GET"])
def get_master_dashboard_stats():
    session = get_db_session()
    try:
        limit = request.args.get("limit", 10, type=int)
        cursor = request.args.get("cursor", type=int)
        limit = max(1, min(limit, 50))

        # Use limit/cursor as part of cache key
        cache_key = f"master_dashboard_stats:limit={limit}:cursor={cursor}"
        if redis_client:
            cached = redis_client.get(cache_key)
            if cached:
                print(f"[Redis] Cache hit for key: {cache_key}")
                import json
                return jsonify(json.loads(cached))
            else:
                print(f"[Redis] Cache miss for key: {cache_key}")

        query = session.query(MasterTable).order_by(MasterTable.id.desc())
        if cursor is not None:
            query = query.filter(MasterTable.id < cursor)
        rows = query.limit(limit).all()

        # Compute stats only for these rows
        total_records = len(rows)
        cities = set()
        areas = set()
        categories = set()
        matched = 0
        unmatched = 0
        missing_phone = 0
        missing_email = 0
        missing_address = 0
        city_counts_dict = {}
        category_counts_dict = {}
        source_stats_dict = {}
        combo_counts_dict = {}

        for row in rows:
            city = getattr(row, 'city', None)
            area = getattr(row, 'area', None)
            category = getattr(row, 'business_category', None)
            data_source = getattr(row, 'data_source', None)
            phone = getattr(row, 'primary_phone', None)
            email = getattr(row, 'email', None)
            address = getattr(row, 'address', None)

            if city: cities.add(city)
            if area: areas.add(area)
            if category: categories.add(category)

            if city and city.strip():
                matched += 1
            else:
                unmatched += 1

            if not phone or not phone.strip():
                missing_phone += 1
            if not email or not email.strip():
                missing_email += 1
            if not address or not address.strip():
                missing_address += 1

            # City counts
            if city:
                city_counts_dict[city] = city_counts_dict.get(city, 0) + 1
            # Category counts
            if category:
                category_counts_dict[category] = category_counts_dict.get(category, 0) + 1
            # Source stats
            if data_source:
                source_stats_dict[data_source] = source_stats_dict.get(data_source, 0) + 1
            # City+Category combo
            if city and category:
                combo_key = (city, category)
                combo_counts_dict[combo_key] = combo_counts_dict.get(combo_key, 0) + 1

        city_counts = [
            {"city": k, "count": v} for k, v in sorted(city_counts_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        category_counts = [
            {"category": k, "count": v} for k, v in sorted(category_counts_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        source_stats = [
            {"source": k, "count": v} for k, v in sorted(source_stats_dict.items(), key=lambda x: x[1], reverse=True)
        ]
        top_city_categories = [
            {"city": k[0], "category": k[1], "count": v} for k, v in sorted(combo_counts_dict.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        stats = {
            "total_records": total_records,
            "total_cities": len(cities),
            "total_areas": len(areas),
            "total_categories": len(categories),
            "city_match_status": {
                "matched": matched,
                "unmatched": unmatched
            },
            "missing_values": {
                "missing_phone": missing_phone,
                "missing_email": missing_email,
                "missing_address": missing_address
            },
            "city_counts": city_counts,
            "category_counts": category_counts,
            "source_stats": source_stats,
            "top_city_categories": top_city_categories
        }

        # Cache the result for 60 seconds
        import json
        if redis_client:
            redis_client.setex(cache_key, 60, json.dumps({"status": "COMPLETED", "stats": stats}))
            print(f"[Redis] Cached stats for key: {cache_key} (TTL: 60s)")

        return jsonify({"status": "COMPLETED", "stats": stats})
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}")
        return jsonify({"status": "ERROR", "message": str(e)}), 500
    finally:
        session.close()

@master_table_bp.route("/master_table/table", methods=["GET"])
def get_master_table_list():
    session = get_db_session()
    try:
        limit = request.args.get("limit", 10, type=int)
        cursor = request.args.get("cursor", type=int)

        limit = max(1, min(limit, 50))

        query = session.query(MasterTable).order_by(MasterTable.id.desc())
        if cursor is not None:
            query = query.filter(MasterTable.id < cursor)

        rows = query.limit(limit + 1).all()

        has_next = len(rows) > limit
        rows = rows[:limit]

        data = [row.to_dict() for row in rows]
        next_cursor = rows[-1].id if rows and has_next else None

        return jsonify({
            "limit": limit,
            "next_cursor": next_cursor,
            "has_next": has_next,
            "data": data
        })
    except Exception as e:
        print(f"Error fetching master table list: {e}")
        return jsonify({"error": "Internal Server Error"}), 500
    finally:
        session.close()