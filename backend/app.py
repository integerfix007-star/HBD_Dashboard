from gevent import monkey
monkey.patch_all()
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import verify_jwt_in_request
from dotenv import load_dotenv

from config import Config
from extensions import db, jwt, cors, mail, migrate, init_redis

# --- Import Models ---
from model.user import User
from model.scraper_task import ScraperTask
from model.googlemap_data import GoogleMapData 
from model.item_csv_model import ItemData
from model.master_table_model import MasterTable
from model.upload_master_reports_model import UploadReport
from model.listing_master import ListingMaster
from model.heyplaces import HeyPlaces
from model.location_master import LocationMaster 

# Existing Models
from model.asklaila import Asklaila
from model.atm import ATM
from model.bank import Bank
from model.college_dunia import CollegeDunia
from model.justdial import JustDial
from model.magicpin import MagicPin
from model.nearbuy import NearBuy
from model.pinda import Pinda
from model.post_office import PostOffice
from model.schoolgis import SchoolGIS
from model.shiksha import Shiksha
from model.yellow_pages import YellowPages
from model.google_map_scrape import GoogleMapScrape

# --- Product Models ---
from model.product_model.amazon_product import AmazonProduct 
from model.product_model.bigbasket_product_model import BigBasketProduct

# --- Import Blueprints ---
from routes.auth_route import auth_bp
from routes.scraper_routes import scraper_bp
from routes.product_routes.product_master_routes.amazon_routes import amazon_api_bp
from routes.product_routes.product_master_routes.bigbasket_routes import bigbasket_api_bp
from routes.product_routes.product_master_routes.blinkit_routes import blinkit_api_bp
from routes.product_routes.product_master_routes.dmart_routes import dmart_api_bp
from routes.product_routes.product_master_routes.flipkart_routes import flipkart_api_bp
from routes.product_routes.product_master_routes.india_mart_routes import india_mart_api_bp
from routes.product_routes.product_master_routes.jio_mart_routes import jio_mart_api_bp
from routes.product_routes.product_master_routes.zepto_routes import zepto_api_bp
from routes.product_routes.product_master_routes.zomato_routes import zomato_api_bp
from routes.googlemap import googlemap_bp 
from routes.master_table import master_table_bp
from routes.upload_product_csv import product_csv_bp
from routes.upload_item_csv import item_csv_bp

# Listing & Product Blueprints
from routes.items_data import item_bp
from routes.item_csv_download import item_csv_bp as item_csv_download_bp
from routes.item_duplicate import item_duplicate_bp
from routes.upload_others_csv import upload_others_csv_bp
from routes.listing_master_route import listing_master_bp
from routes.location_master_route import location_master_bp 

# Sub-folder listing routes
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

# Product sub-routes
from routes.product_routes.product_uploaders_routes.upload_amazon_products_route import amazon_bp as amazon_upload_bp
from routes.product_routes.product_uploaders_routes.upload_vivo_route import vivo_bp
from routes.product_routes.product_uploaders_routes.upload_big_basket_route import bigbasket_bp
from routes.product_routes.product_uploaders_routes.upload_blinkit_route import blinkit_bp
from routes.product_routes.product_uploaders_routes.upload_dmart_route import dmart_bp
from routes.product_routes.product_uploaders_routes.upload_flipkart_products_route import flipkart_bp
from routes.product_routes.product_uploaders_routes.upload_india_mart_route import indiamart_bp
from routes.product_routes.product_uploaders_routes.upload_jio_mart_route import jiomart_bp
from routes.product_master_route import product_master_bp
# New Dashboard Blueprints
from routes.gdrive_etl_routes.validation_dashboard import validation_dashboard_bp
from routes.gdrive_etl_routes.dashboard_stats import dashboard_bp

# --- Initialize App ---
load_dotenv(override=True)
app = Flask(__name__)
app.config.from_object(Config)

# Init extensions
db.init_app(app)
migrate.init_app(app, db)
jwt.init_app(app)
cors.init_app(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True) 
mail.init_app(app)
init_redis(app)

with app.app_context():
    db.create_all()

def _run_startup_checks():
    """DB connection test + migrations. Called once when the server is ready."""
    with app.app_context():
        try:
            db.session.execute(db.text('SELECT 1'))
            print(f"✅ DATABASE CONNECTION: SUCCESS (Host: {app.config.get('DB_HOST', 'unknown')})")
        except Exception as e:
            print(f"❌ DATABASE CONNECTION: FAILED! Error: {e}")

        try:
            from utils.db_migrations import run_pending_migrations
            print("🔄 Running Database Migrations...")
            run_pending_migrations(app)
        except ImportError:
            pass

# For WSGI servers (gunicorn, passenger) — run checks on import since there's no reloader
if os.environ.get('WERKZEUG_RUN_MAIN') is None and __name__ != '__main__':
    _run_startup_checks()

# --- GLOBAL JWT PROTECTION ---
PUBLIC_ROUTES = [
    "/",
    "/auth/signup",
    "/auth/login",
    "/auth/logout",
    "/auth/forgot-password",
    "/auth/verify-otp",
    "/auth/reset-password",
    "/health",
    "/master_table/list",
    "/master-dashboard-stats",
    "/atm/fetch-data",
    "/bank/fetch-data",
    "/asklaila/fetch-data",
    "/college-dunia/fetch-data",
    "/google-map/fetch-data",
    "/listing-master",
    "/complete-data",
    "/heyplaces/fetch-data",
    "/justdial/fetch-data",
    "/magicpin/fetch-data",
    "/nearbuy/fetch-data",
    "/pinda/fetch-data",
    "/post-office/fetch-data",
    "/schoolgis/fetch-data",
    "/shiksha/fetch-data",
    "/yellow-pages/fetch-data",
    "/google-map-scrape/fetch-data",
    "/amazon/fetch-data",
    "/big-basket/fetch-data",
    "/location-master/fetch-data",
    "/validation/dashboard",
    "/product-master/fetch-data",
    "/api/amazon/fetch-data",
    "/api/big-basket/fetch-data",
    "/api/blinkit/fetch-data",
    "/api/dmart/fetch-data",
    "/api/flipkart/fetch-data",
    "/api/india-mart/fetch-data",
    "/api/jio-mart/fetch-data",
    "/api/zepto/fetch-data",
    "/api/zomato/fetch-data",
]

@app.before_request
def protect_all_routes():
    if request.method == "OPTIONS":
        return jsonify({"message": "CORS preflight successful"}), 200

    normalized_path = request.path.rstrip('/')
    public_paths = [route.rstrip('/') for route in PUBLIC_ROUTES]

    # Bypass for whitelist or any fetch-data route
    if normalized_path in public_paths or normalized_path.endswith('/fetch-data'):
        return None

    try:
        verify_jwt_in_request()
    except Exception as e:
        print(f"❌ JWT REJECTED for {request.path}: {str(e)}")
        return jsonify({"message": "Missing or invalid token", "error": str(e)}), 401

# --- Register Blueprints ---
# As requested, we follow the working file's lead: no manual '/api' addition here 
# if Nginx handles it.
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(scraper_bp, url_prefix="/api")
app.register_blueprint(googlemap_bp, url_prefix='/api')
app.register_blueprint(master_table_bp)
app.register_blueprint(product_csv_bp)
app.register_blueprint(item_csv_bp)
app.register_blueprint(item_bp, url_prefix="/items")
app.register_blueprint(item_csv_download_bp)
app.register_blueprint(item_duplicate_bp)
app.register_blueprint(upload_others_csv_bp)
app.register_blueprint(listing_master_bp, url_prefix="/api")
app.register_blueprint(validation_dashboard_bp, url_prefix="/validation")
app.register_blueprint(dashboard_bp, url_prefix="/stats")
app.register_blueprint(product_master_bp, url_prefix="/product-master")


# --- Register Product Master Data Routes (Batch) ---
product_master_routes = [
    (amazon_api_bp, "/api/amazon"),
    (bigbasket_api_bp, "/api/big-basket"),
    (blinkit_api_bp, "/api/blinkit"),
    (dmart_api_bp, "/api/dmart"),
    (flipkart_api_bp, "/api/flipkart"),
    (india_mart_api_bp, "/api/india-mart"),
    (jio_mart_api_bp, "/api/jio-mart"),
    (zepto_api_bp, "/api/zepto"),
    (zomato_api_bp, "/api/zomato"),
]

for bp, prefix in product_master_routes:
    app.register_blueprint(bp, url_prefix=prefix)

# --- Register Listing & Product Blueprints (Batch) ---
blueprints_listing = [
    (asklaila_bp, "/asklaila"), (atm_bp, "/atm"), (bank_bp, "/bank"),
    (college_dunia_bp, "/college-dunia"), (freelisting_bp, "/freelisting"),
    (gmap_upload_bp, "/google-map"), (google_map_scrape_bp, "/google-map-scrape"),
    (heyplaces_bp, "/heyplaces"), (justdial_bp, "/justdial"), (magicpin_bp, "/magicpin"),
    (nearbuy_bp, "/nearbuy"), (pinda_bp, "/pinda"), (post_office_bp, "/post-office"),
    (schoolgis_bp, "/schoolgis"), (shiksha_bp, "/shiksha"), (yellow_pages_bp, "/yellow-pages"),
    (amazon_upload_bp, "/api/amazon"), (vivo_bp, "/api/vivo"), (blinkit_bp, "/api/blinkit"),
    (dmart_bp, "/api/dmart"), (flipkart_bp, "/api/flipkart"), (indiamart_bp, "/api/india-mart"),
    (jiomart_bp, "/api/jio-mart"), (bigbasket_bp, "/api/big-basket"),
    (location_master_bp, "/location-master")
]

for bp, prefix in blueprints_listing:
    # Product upload routes have /api prefix, listing routes don't
    app.register_blueprint(bp, url_prefix=prefix)

@app.route('/')
def index():
    return jsonify({"message": "Flask API is running! Clean and Modular."})

if __name__ == '__main__':
    # In debug mode, Werkzeug reloader runs the module twice:
    # 1) Parent process (spawns the child) — WERKZEUG_RUN_MAIN is NOT set
    # 2) Child process (serves requests)  — WERKZEUG_RUN_MAIN='true'
    # Run startup checks only in the child to avoid duplicate logs.
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        _run_startup_checks()
    app.run(host='0.0.0.0', port=8090, debug=True)