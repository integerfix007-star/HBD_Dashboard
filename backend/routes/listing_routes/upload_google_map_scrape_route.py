from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_google_map_scrape_task import process_google_map_scrape_task
from werkzeug.utils import secure_filename
import os 

google_map_scrape_bp = Blueprint('google_map_scrape_bp',__name__)

UPLOAD_DIR = "tmp/uploads/google_map_scrape"
os.makedirs(UPLOAD_DIR,exist_ok=True)

@google_map_scrape_bp.route('/upload/google-map-scrape-data', methods=["POST"])
def upload_google_map_scrape_route():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error":"No files provided"}),400
    paths = []
    for f in files:
        file_name = secure_filename(f.filename)
        file_path = os.path.join(UPLOAD_DIR,file_name)
        f.save(file_path)
        paths.append(file_path)
    try:
        task = process_google_map_scrape_task.delay(paths)
        return jsonify({
            "status":"file_accepted",
            "task_id":task.id
        }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500
