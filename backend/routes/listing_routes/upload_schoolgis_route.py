from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_schoolgis_task import process_schoolgis_task
from werkzeug.utils import secure_filename  
import os 

UPLOAD_DIR = "tmp/uploads/schoolgis"
os.makedirs(UPLOAD_DIR,exist_ok=True)

schoolgis_bp = Blueprint("schoolgis_bp",__name__)
@schoolgis_bp.route("/upload/schoolgis-data",methods=["POST"])
def upload_schoolgis_route():
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
        task = process_schoolgis_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id": task.id
            }), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500