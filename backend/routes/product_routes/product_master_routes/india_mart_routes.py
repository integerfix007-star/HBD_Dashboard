from flask import Blueprint, request, jsonify
import threading
from extensions import db
from model.product_model.product_indiamart_model import IndiaMartProduct
from services.scrapers.amazon_service import scrape_amazon_search

india_mart_api_bp = Blueprint('india_mart_api_bp', __name__)

# --- ROUTE 1: Start Scraping ---
@india_mart_api_bp.route('/scrape', methods=['POST'])
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
@india_mart_api_bp.route('/fetch-data', methods=['GET']) 
def get_india_mart_data():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '', type=str).strip()
        category = request.args.get('category', '', type=str).strip()
        brand = request.args.get('brand', '', type=str).strip()
        status = request.args.get('status', '', type=str).strip()
        seller_name = request.args.get('seller_name', '', type=str).strip()
        supplier_level = request.args.get('supplier_level', '', type=str).strip()
        min_order = request.args.get('min_order', '', type=str).strip()
        
        # Validate pagination
        page = max(1, page)
        limit = max(1, min(limit, 100))  # Cap at 100 per page
        
        # Build base query
        query = IndiaMartProduct.query
        
        # Apply filters safely using model column names
        if search and hasattr(IndiaMartProduct, 'Name'):
            query = query.filter(IndiaMartProduct.Name.ilike(f'%{search}%'))
        
        if category and hasattr(IndiaMartProduct, 'Product_Subcategory'):
            query = query.filter(IndiaMartProduct.Product_Subcategory.ilike(f'%{category}%'))
        
        if brand and hasattr(IndiaMartProduct, 'Brand'):
            query = query.filter(IndiaMartProduct.Brand.ilike(f'%{brand}%'))
        
        if status and hasattr(IndiaMartProduct, 'Status'):
            query = query.filter(IndiaMartProduct.Status.ilike(f'%{status}%'))
        
        if seller_name and hasattr(IndiaMartProduct, 'Seller_Name'):
            query = query.filter(IndiaMartProduct.Seller_Name.ilike(f'%{seller_name}%'))
        
        if supplier_level and hasattr(IndiaMartProduct, 'Supplier_Verif_Level'):
            query = query.filter(IndiaMartProduct.Supplier_Verif_Level.ilike(f'%{supplier_level}%'))
        
        if min_order and hasattr(IndiaMartProduct, 'Min_Order_Value'):
            query = query.filter(IndiaMartProduct.Min_Order_Value.ilike(f'%{min_order}%'))
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        products = query.order_by(IndiaMartProduct.id.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # Serialize using to_dict()
        results = [p.to_dict() for p in products]
        
        # Calculate pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            "message": "IndiaMART products fetched successfully",
            "data": results,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": limit
        }), 200
    except Exception as e:
        import traceback
        print(f"IndiaMART Error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'message': 'Failed to fetch IndiaMART products'}), 500