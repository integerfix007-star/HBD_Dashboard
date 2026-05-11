from flask import Blueprint, request, jsonify
import threading
from extensions import db
from model.product_model.product_zomato_model import ZomatoProduct
from services.scrapers.amazon_service import scrape_amazon_search

zomato_api_bp = Blueprint('zomato_api_bp', __name__)

# --- ROUTE 1: Start Scraping ---
@zomato_api_bp.route('/scrape', methods=['POST'])
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
@zomato_api_bp.route('/fetch-data', methods=['GET']) 
def get_zomato_data():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '', type=str).strip()
        category = request.args.get('category', '', type=str).strip()
        brand = request.args.get('brand', '', type=str).strip()
        status = request.args.get('status', '', type=str).strip()
        seller_name = request.args.get('seller_name', '', type=str).strip()
        restaurant_id = request.args.get('restaurant_id', '', type=str).strip()
        menu_category = request.args.get('menu_category', '', type=str).strip()
        
        # Validate pagination
        page = max(1, page)
        limit = max(1, min(limit, 100))  # Cap at 100 per page
        
        # Build base query
        query = ZomatoProduct.query
        
        # Apply filters safely using model column names
        if search and hasattr(ZomatoProduct, 'Name'):
            query = query.filter(ZomatoProduct.Name.ilike(f'%{search}%'))
        
        if category and hasattr(ZomatoProduct, 'Product_Subcategory'):
            query = query.filter(ZomatoProduct.Product_Subcategory.ilike(f'%{category}%'))
        
        if brand and hasattr(ZomatoProduct, 'Brand'):
            query = query.filter(ZomatoProduct.Brand.ilike(f'%{brand}%'))
        
        if status and hasattr(ZomatoProduct, 'Status'):
            query = query.filter(ZomatoProduct.Status.ilike(f'%{status}%'))
        
        if seller_name and hasattr(ZomatoProduct, 'Seller_Name'):
            query = query.filter(ZomatoProduct.Seller_Name.ilike(f'%{seller_name}%'))
        
        if restaurant_id and hasattr(ZomatoProduct, 'Restaurant_ID'):
            query = query.filter(ZomatoProduct.Restaurant_ID.ilike(f'%{restaurant_id}%'))
        
        if menu_category and hasattr(ZomatoProduct, 'Menu_Item_Category'):
            query = query.filter(ZomatoProduct.Menu_Item_Category.ilike(f'%{menu_category}%'))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        products = query.order_by(ZomatoProduct.id.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # Serialize using to_dict()
        results = [p.to_dict() for p in products]
        
        # Calculate pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            "message": "Zomato products fetched successfully",
            "data": results,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": limit
        }), 200
    except Exception as e:
        import traceback
        print(f"Zomato Error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'message': 'Failed to fetch Zomato products'}), 500