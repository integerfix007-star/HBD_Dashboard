from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from extensions import db, jwt, cors

# 1. Import New Blueprints (The ones we just created)
from routes.scraper_routes import scraper_bp
from routes.amazon_routes import amazon_api_bp

# 2. Import Existing Blueprints (Your original routes)
from routes.auth_route import auth_bp
from routes.googlemap import googlemap_bp
from routes.master_table import master_table_bp
from routes.upload_product_csv import product_csv_bp
from routes.upload_item_csv import item_csv_bp
from routes.amazon_product import amazon_products_bp
from routes.items_data import item_bp
from routes.item_csv_download import item_csv_bp as item_csv_download_bp
from routes.item_duplicate import item_duplicate_bp
from routes.upload_others_csv import upload_others_csv_bp

# 3. Import All Listing Blueprints
from routes.listing_routes.upload_asklaila_route import asklaila_bp
from routes.listing_routes.upload_atm_route import atm_bp
from routes.listing_routes.upload_bank_route import bank_bp
from routes.listing_routes.upload_college_dunia_route import college_dunia_bp
from routes.listing_routes.upload_freelisting_route import freelisting_bp
from routes.listing_routes.upload_google_map_route import google_map_bp as gmap_upload_bp
from routes.listing_routes.upload_google_map_scrape_route import google_map_scrape_bp
from routes.listing_routes.upload_heyplaces_route import heyplaces_bp
from routes.listing_routes.upload_justdial_route import justdial_bp
from routes.listing_routes.upload_magicpin_route import magicpin_bp
from routes.listing_routes.upload_nearbuy_route import nearbuy_bp
from routes.listing_routes.upload_pinda_route import pinda_bp
from routes.listing_routes.upload_post_office_route import post_office_bp
from routes.listing_routes.upload_schoolgis_route import schoolgis_bp
from routes.listing_routes.upload_shiksha_route import shiksha_bp
from routes.listing_routes.upload_yellow_pages_route import yellow_pages_bp

# 4. Import Product Upload Blueprints
from routes.product_routes.upload_amazon_products_route import amazon_bp as amazon_upload_bp
from routes.product_routes.upload_vivo_route import vivo_bp
from routes.product_routes.upload_big_basket_route import upload_big_basket_route
from routes.product_routes.upload_blinkit_route import blinkit_bp
from routes.product_routes.upload_dmart_route import dmart_bp
from routes.product_routes.upload_flipkart_products_route import flipkart_bp
from routes.product_routes.upload_india_mart_route import indiamart_bp
from routes.product_routes.upload_jio_mart_route import jiomart_bp

# --- Initialize App ---
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Extensions
CORS(app)  # Global CORS
db.init_app(app)
jwt.init_app(app)
cors(app) # Extension CORS if specific

# Create Tables
# Import models to ensure they are registered with SQLAlchemy
from model.user import User
from model.scraper_task import ScraperTask
from model.amazon_product_model import AmazonProduct
# Add other models here as needed for creation...

with app.app_context():
    db.create_all()

# --- Register Blueprints ---

# New Scrapers
app.register_blueprint(scraper_bp)        # Handles /api/tasks, /api/scrape
app.register_blueprint(amazon_api_bp)     # Handles /api/amazon_products, /api/scrape_amazon

# Core Routes
app.register_blueprint(auth_bp)
app.register_blueprint(googlemap_bp)
app.register_blueprint(master_table_bp)
app.register_blueprint(product_csv_bp)
app.register_blueprint(item_csv_bp)
app.register_blueprint(amazon_products_bp)
app.register_blueprint(item_bp, url_prefix="/items")
# app.register_blueprint(item_csv_download_bp) # Uncomment if file exists
app.register_blueprint(item_duplicate_bp)
app.register_blueprint(upload_others_csv_bp)

# Bulk Listing Uploads
listing_blueprints = [
    (asklaila_bp, "/asklaila"), (atm_bp, "/atm"), (bank_bp, "/bank"),
    (college_dunia_bp, "/college-dunia"), (freelisting_bp, "/freelisting"),
    (gmap_upload_bp, "/google-map-upload"), (google_map_scrape_bp, "/google-map-scrape"),
    (heyplaces_bp, "/heyplaces"), (justdial_bp, "/justdial"), (magicpin_bp, "/magicpin"),
    (nearbuy_bp, "/nearbuy"), (pinda_bp, "/pinda"), (post_office_bp, "/post-office"),
    (schoolgis_bp, "/schoolgis"), (shiksha_bp, "/shiksha"), (yellow_pages_bp, "/yellow-pages"),
    (amazon_upload_bp, "/amazon-upload"), (vivo_bp, "/vivo"), (blinkit_bp, "/blinkit"),
    (dmart_bp, "/dmart"), (flipkart_bp, "/flipkart"), (indiamart_bp, "/india-mart"),
    (jiomart_bp, "/jio-mart")
]

for bp, prefix in listing_blueprints:
    app.register_blueprint(bp, url_prefix=prefix)

@app.route('/')
def index():
   return jsonify({"message": "Flask API is running! Clean and Modular."})

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=8000, debug=True)