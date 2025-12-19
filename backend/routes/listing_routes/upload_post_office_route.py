from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_post_office_task import process_post_office_task
from werkzeug.utils import secure_filename 
import os 

UPLOAD_DIR = "tmp/uploads/post_office"
os.makedirs(UPLOAD_DIR, exist_ok=True)

post_office_bp = Blueprint('post_office_bp', __name__)

@post_office_bp.route('/upload/post-office-data', methods=["POST"])
def upload_post_office_route():
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
        task = process_post_office_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500