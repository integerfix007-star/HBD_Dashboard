from flask import Blueprint, request, jsonify
import threading
from extensions import db
from model.product_model.product_blinkit_model import BlinkitProduct
from services.scrapers.amazon_service import scrape_amazon_search

blinkit_api_bp = Blueprint('blinkit_api_bp', __name__)

# --- ROUTE 1: Start Scraping ---
@blinkit_api_bp.route('/scrape', methods=['POST'])
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
@blinkit_api_bp.route('/fetch-data', methods=['GET']) 
def get_blinkit_data():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '', type=str).strip()
        category = request.args.get('category', '', type=str).strip()
        brand = request.args.get('brand', '', type=str).strip()
        status = request.args.get('status', '', type=str).strip()
        seller_name = request.args.get('seller_name', '', type=str).strip()
        
        # Validate pagination
        page = max(1, page)
        limit = max(1, min(limit, 100))  # Cap at 100 per page
        
        # Build base query
        query = BlinkitProduct.query
        
        # Apply filters safely using model column names
        if search and hasattr(BlinkitProduct, 'Name'):
            query = query.filter(BlinkitProduct.Name.ilike(f'%{search}%'))
        
        if category and hasattr(BlinkitProduct, 'Product_Subcategory'):
            query = query.filter(BlinkitProduct.Product_Subcategory.ilike(f'%{category}%'))
        
        if brand and hasattr(BlinkitProduct, 'Brand'):
            query = query.filter(BlinkitProduct.Brand.ilike(f'%{brand}%'))
        
        if status and hasattr(BlinkitProduct, 'Status'):
            query = query.filter(BlinkitProduct.Status.ilike(f'%{status}%'))
        
        if seller_name and hasattr(BlinkitProduct, 'Seller_Name'):
            query = query.filter(BlinkitProduct.Seller_Name.ilike(f'%{seller_name}%'))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        products = query.order_by(BlinkitProduct.id.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # Serialize using to_dict()
        results = [p.to_dict() for p in products]
        
        # Calculate pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            "message": "Blinkit products fetched successfully",
            "data": results,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": limit
        }), 200
    except Exception as e:
        import traceback
        print(f"Blinkit Error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'message': 'Failed to fetch Blinkit products'}), 500