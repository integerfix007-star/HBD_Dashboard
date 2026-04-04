from flask import Blueprint, request, jsonify
import threading
from extensions import db
from model.product_model.product_zepto_model import ZeptoProduct
from services.scrapers.amazon_service import scrape_amazon_search

zepto_api_bp = Blueprint('zepto_api_bp', __name__)

# --- ROUTE 1: Start Scraping ---
@zepto_api_bp.route('/scrape', methods=['POST'])
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
@zepto_api_bp.route('/fetch-data', methods=['GET']) 
def zepto_data():
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '', type=str).strip()
        category = request.args.get('category', '', type=str).strip()
        brand = request.args.get('brand', '', type=str).strip()
        status = request.args.get('status', '', type=str).strip()
        seller_name = request.args.get('seller_name', '', type=str).strip()
        payment_status = request.args.get('payment_status', '', type=str).strip()
        delivery_fee = request.args.get('delivery_fee', '', type=str).strip()
        
        # Validate pagination
        page = max(1, page)
        limit = max(1, min(limit, 100))  # Cap at 100 per page to prevent abuse
        
        # Build query
        query = ZeptoProduct.query
        
        # Apply filters safely using model column names
        if search:
            query = query.filter(ZeptoProduct.Name.ilike(f'%{search}%'))
        
        if category:
            query = query.filter(ZeptoProduct.Product_Subcategory.ilike(f'%{category}%'))
        
        if brand and hasattr(ZeptoProduct, 'Brand'):
            query = query.filter(ZeptoProduct.Brand.ilike(f'%{brand}%'))
        
        if status and hasattr(ZeptoProduct, 'Status'):
            query = query.filter(ZeptoProduct.Status.ilike(f'%{status}%'))
        
        if seller_name and hasattr(ZeptoProduct, 'Seller_Name'):
            query = query.filter(ZeptoProduct.Seller_Name.ilike(f'%{seller_name}%'))
        
        if payment_status and hasattr(ZeptoProduct, 'payment_status'):
            query = query.filter(ZeptoProduct.payment_status.ilike(f'%{payment_status}%'))
        
        if delivery_fee and hasattr(ZeptoProduct, 'delivery_fee'):
            query = query.filter(ZeptoProduct.delivery_fee.ilike(f'%{delivery_fee}%'))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting and pagination
        products = query.order_by(ZeptoProduct.id.desc()).offset((page - 1) * limit).limit(limit).all()
        
        # Serialize using to_dict() method from model
        results = [p.to_dict() for p in products]
        
        # Calculate total pages
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        return jsonify({
            "message": "Zepto products fetched successfully",
            "data": results,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "per_page": limit
        }), 200
    except Exception as e:
        import traceback
        print(f"Zepto Error: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'message': 'Failed to fetch Zepto products'}), 500