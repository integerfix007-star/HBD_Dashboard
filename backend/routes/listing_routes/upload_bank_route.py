from flask import Flask,request,jsonify,Blueprint
from tasks.listings_task.upload_bank_task import process_bank_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/bank"
os.makedirs(UPLOAD_DIR,exist_ok=True)

bank_bp = Blueprint('bank_bp', __name__)
@bank_bp.route('/upload/bank-data', methods=['POST'])
def upload_bank_route():
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
        task = process_bank_task.delay(paths)
        return jsonify({
            "status":"file_accepted",
            "task_id":task.id
        }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500