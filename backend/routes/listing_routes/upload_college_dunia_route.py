from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_college_dunia_task import process_college_dunia_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/college_dunia"
os.makedirs(UPLOAD_DIR,exist_ok=True)

college_dunia_bp = Blueprint('college_dunia_bp', __name__)
@college_dunia_bp.route('/upload/college-dunia-data', methods=['POST'])

def upload_college_dunia_data_route():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files provided"}), 400
    paths = []
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_DIR, filename)
        file.save(file_path)
        paths.append(file_path)
    try:
        task = process_college_dunia_task.delay(paths)
        return jsonify({"status":"files_accepted","task_id": task.id}), 202
    except Exception as e:
        return jsonify({"error": str(e)}), 500