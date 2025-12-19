from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_nearbuy_task import process_nearbuy_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/nearbuy"
os.makedirs(UPLOAD_DIR,exist_ok=True)

nearbuy_bp = Blueprint('nearbuy_bp', __name__)

@nearbuy_bp.route('/upload/nearbuy-data', methods=['POST'])
def upload_nearbuy_route():
    files = request.files.getlist('file')
    if not files:
        return jsonify({"error": "No files provided"}), 400
    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        f.save(file_path)
        paths.append(file_path)
    try:
        task = process_nearbuy_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    