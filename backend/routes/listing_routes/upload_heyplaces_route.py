from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_heyplaces_task import process_heyplaces_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = 'tmp/uploads/heyplaces'
os.makedirs(UPLOAD_DIR,exist_ok=True)

heyplaces_bp = Blueprint('heyplaces_bp', __name__)

@heyplaces_bp.route('/upload/heyplaces-data', methods=["POST"])
def upload_heyplaces_route():
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
        task = process_heyplaces_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500