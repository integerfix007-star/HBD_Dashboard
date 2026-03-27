from flask import Blueprint, request, jsonify
import threading
from extensions import db
from model.product_model.dmart_product_model import DMartProduct
from services.scrapers.amazon_service import scrape_amazon_search

dmart_api_bp = Blueprint('dmart_api_bp', __name__)

# --- ROUTE 1: Start Scraping ---
@dmart_api_bp.route('/scrape', methods=['POST'])
def scrape_and_insert():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        search_term = data.get('search_term')
        pages = int(data.get('pages', 1))
        
        if not search_term:
            return jsonify({'error': 'search_term is required'}), 400
            
        # Start the service via Celery to avoid worker multiplication issues
        from tasks.products_task.amazon_scraper_task import run_amazon_scraper
        run_amazon_scraper.delay(search_term, pages)
        
        return jsonify({"status": "started", "message": f"Scraping '{search_term}' started via Celery"}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- ROUTE 2: Fetch Data (Using SQLAlchemy) with Pagination & Filtering ---
@dmart_api_bp.route('/fetch-data', methods=['GET']) 
def get_dmart_data():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '', type=str)
        category = request.args.get('category', '', type=str)
        
        # Validate pagination
        page = max(1, page)
        limit = max(1, min(limit, 100))  # Cap at 100 per page to prevent abuse
        
        # Build query
        query = DMartProduct.query
        
        # Apply filters
        if search:
            query = query.filter(DMartProduct.Product_name.ilike(f'%{search}%'))
        
        if category:
            query = query.filter(DMartProduct.category.ilike(f'%{category}%'))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting and pagination
        products = query.order_by(DMartProduct.id.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # Serialize using to_dict() method from model
        results = [p.to_dict() for p in products]
        
        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            "data": results,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": limit
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500