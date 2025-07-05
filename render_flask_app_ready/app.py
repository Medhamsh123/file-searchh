import os
from flask import Flask, request, jsonify, send_file, send_from_directory, redirect
from pymongo import MongoClient
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import mimetypes

load_dotenv()
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{MONGO_DB}?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = db["files"]

app = Flask(__name__)
BASE_DIR = os.getcwd()
app.config["UPLOAD_FOLDER"] = BASE_DIR

@app.route("/files")
def get_files():
    files = list(collection.find({}, {"_id": 0}))
    return jsonify(files)

@app.route("/download/<path:subpath>")
def download_file(subpath):
    full_path = os.path.join(BASE_DIR, subpath)
    return send_file(full_path, as_attachment=True)

@app.route("/preview/<path:subpath>")
def preview_file(subpath):
    full_path = os.path.join(BASE_DIR, subpath)
    mime_type, _ = mimetypes.guess_type(full_path)
    return send_file(full_path, mimetype=mime_type)

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")
    tags = request.form.get("tags", "")
    tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(BASE_DIR, filename)
        file.save(save_path)

        mime_type, _ = mimetypes.guess_type(save_path)
        size = os.path.getsize(save_path)
        modified = datetime.fromtimestamp(os.path.getmtime(save_path)).strftime("%Y-%m-%d %H:%M:%S")

        doc = {
            "name": filename,
            "path": save_path,
            "relative_path": os.path.relpath(save_path, BASE_DIR),
            "type": mime_type or "Unknown",
            "size": f"{round(size / 1024, 2)} KB",
            "modified": modified,
            "tags": tag_list
        }
        collection.insert_one(doc)
    return redirect("/")

@app.route("/")
def index():
    return send_from_directory('.', 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
