from flask import Blueprint, request, jsonify
from model.googlemap_data import GoogleMapData 

googlemap_bp = Blueprint('googlemap', __name__)

@googlemap_bp.route("/google-listings", methods=["GET"])
def get_google_listings():
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search = request.args.get('search', '').strip()
        city = request.args.get('city', '').strip()

        query = GoogleMapData.query

        if search:
            query = query.filter(GoogleMapData.business_name.ilike(f"%{search}%"))
        
        if city:
            # Added a null check (.isnot(None)) to prevent database crashes
            query = query.filter(
                GoogleMapData.address.isnot(None),
                GoogleMapData.address.ilike(f"%{city}%")
            )

        paginated_data = query.order_by(GoogleMapData.id.desc()).paginate(
            page=page, 
            per_page=limit, 
            error_out=False
        )

        return jsonify({
            "data": [item.to_dict() for item in paginated_data.items],
            "total_count": paginated_data.total,
            "total_pages": paginated_data.pages,
            "current_page": page
        })

    except Exception as e:
        print(f"❌ Backend Error: {str(e)}") 
        return jsonify({"error": "Internal Server Error"}), 500