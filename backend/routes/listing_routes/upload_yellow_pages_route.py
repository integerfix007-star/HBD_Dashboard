from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_yellow_pages_task import process_yellow_pages_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/yellow_pages"
os.makedirs(UPLOAD_DIR,exist_ok=True)

yellow_pages_bp = Blueprint("yellow_pages_bp",__name__)

@yellow_pages_bp.route("upload/yellow-pages-data",methods=["POST"])
def upload_yellow_pages_upload():
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
        task = process_yellow_pages_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id":task.id
            }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500