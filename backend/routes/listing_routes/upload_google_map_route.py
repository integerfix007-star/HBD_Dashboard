from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_google_map_task import process_google_map_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/google_map"
os.makedirs(UPLOAD_DIR,exist_ok=True)

google_map_bp = Blueprint("google_map_bp",__name__)
@google_map_bp.route("/upload/google-map-data",methods=["POST"])
def upload_google_map_route():
    files = request.files.getlist("file")
    if not files:
        return jsonify({"error":"No files provided"}),400
    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        filepath = os.path.join(UPLOAD_DIR, filename)
        f.save(filepath)
        paths.append(filepath)
    try:
        task = process_google_map_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500
