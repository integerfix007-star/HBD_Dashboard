from flask import Flask,request,jsonify,Blueprint
from tasks.products_task.upload_amazon_products_task import process_amazon_products_task
from werkzeug.utils import secure_filename
import os 

UPLOAD_DIR = "tmp/uploads/amazon_products"
os.makedirs(UPLOAD_DIR,exist_ok=True)

amazon_products_bp = Blueprint("amazon_products_bp",__name__)
@amazon_products_bp.route("/upload/amazon-products-data",methods=["POST"])

def upload_amazon_products_route():
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
        task = process_amazon_products_task.delay(paths)
        return jsonify({
            "status":"files_accepted",
            "task_id":task.id
            }),202
    except Exception as e:
        return jsonify({
            "error":str(e)
        }),500