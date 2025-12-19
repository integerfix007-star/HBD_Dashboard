from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_pinda_task import process_pinda_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/pinda"
os.makedirs(UPLOAD_DIR,exist_ok=True)

pinda_bp = Blueprint('pinda_bp', __name__)
@pinda_bp.route('/upload/pinda-data', methods=['POST'])
def upload_pinda_route():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files provided"}), 400
    paths = []
    for f in files:
        filename = secure_filename(f.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        f.save(file_path)
        paths.append(file_path)
    try:
        task = process_pinda_task.delay(paths)
        return jsonify({"status":"files_accepted","task_id": task.id}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500