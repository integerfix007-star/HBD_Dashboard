from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_justdial_task import process_justdial_task
from werkzeug.utils import secure_filename  
import os 

UPLOAD_DIR = "tmp/uploads/justdial"
os.makedirs(UPLOAD_DIR,exist_ok=True)

justdial_bp = Blueprint('justdial_bp', __name__)

@justdial_bp.route('/upload/justdial-data', methods=["POST"])
def upload_justdial_route():
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
        task = process_justdial_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500