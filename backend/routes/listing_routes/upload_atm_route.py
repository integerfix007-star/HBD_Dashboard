from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_atm_task import process_atm_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/atm"
os.makedirs(UPLOAD_DIR,exist_ok=True)

atm_bp = Blueprint("atm_bp",__name__)

@atm_bp.route('/upload/atm-data',methods=["POST"])
def upload_atm_route():
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
        task = process_atm_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500