from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_freelisting_task import process_freelisting_task
from werkzeug.utils import secure_filename
import os 

freelisting_bp = Blueprint('freelisting_bp',__name__)

UPLOAD_DIR = 'tmp/uploads/freelisting' 
os.makedirs(UPLOAD_DIR, exist_ok=True)

@freelisting_bp.route('/upload/freelisting-data', methods=["POST"])
def upload_freelisting_route():
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
        task = process_freelisting_task.delay(paths)
        return jsonify({
            "status":"file_accepted",
            "task_id":task.id
        }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500