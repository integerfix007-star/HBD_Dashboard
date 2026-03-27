from flask import Flask,request,jsonify,Blueprint
from tasks.products_task.upload_big_basket_task import upload_big_basket_data
from werkzeug.utils import secure_filename
import os 
from utils.storage import get_upload_base_dir

bigbasket_bp = Blueprint('bigbasket_bp', __name__)

@bigbasket_bp.route('/upload/bigbasket-data', methods=['POST'])
def upload_bigbasket_data():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400
    UPLOAD_DIR = get_upload_base_dir() / "bigbasket"
    paths = []
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    for f in files : 
        filename = secure_filename(f.filename)
        filepath = UPLOAD_DIR / filename
        f.save(filepath)
        paths.append(str(filepath))
    try:
       task = upload_big_basket_data.delay(paths)
       return jsonify({
           "status": "files_accepted",
           "task_id" : task.id
       }), 202
    except Exception as e:
        print(f"❌ error in bigbasket uploader route: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500