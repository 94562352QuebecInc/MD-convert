#!/usr/bin/env python3
"""
app.py — Flask web interface for mdconver.py
Port: 4000
"""

import datetime
import json
import os
import subprocess
import sys
import threading

from flask import (Flask, Response, abort, jsonify, render_template,
                   request, send_from_directory)
from werkzeug.utils import secure_filename


def safe_path(directory: str, filename: str) -> str:
    """
    Return the absolute path of `filename` inside `directory`.
    Raises 404 if the resolved path escapes the directory (traversal guard).
    Uses os.path.basename so the filename is preserved as-is (no
    secure_filename mangling) while still being safe.
    """
    name  = os.path.basename(filename)   # strip any path components
    path  = os.path.realpath(os.path.join(directory, name))
    root  = os.path.realpath(directory)
    if not path.startswith(root + os.sep) and path != root:
        abort(400, "Invalid filename")
    return path

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
PDF_DIR    = os.path.join(BASE_DIR, "PDFs")
OUTPUT_DIR = os.path.join(BASE_DIR, "Outputs")
LOG_DIR    = os.path.join(OUTPUT_DIR, "logs")

SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx", ".xlsx", ".xls"}

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB upload limit

os.makedirs(PDF_DIR,    exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR,    exist_ok=True)

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/uploads", methods=["GET"])
def list_uploads():
    """List all files in PDFs/."""
    files = []
    for f in sorted(os.listdir(PDF_DIR)):
        path = os.path.join(PDF_DIR, f)
        if os.path.isfile(path) and os.path.splitext(f)[1].lower() in SUPPORTED_EXTENSIONS:
            files.append({
                "name": f,
                "size": os.path.getsize(path),
                "modified": datetime.datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).strftime("%Y-%m-%d %H:%M"),
            })
    return jsonify(files)


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload one or more documents to PDFs/."""
    if "files" not in request.files:
        return jsonify({"error": "No files part"}), 400
    uploaded = []
    errors   = []
    for file in request.files.getlist("files"):
        if not file.filename:
            continue
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            errors.append(f"{file.filename}: unsupported file type ({ext})")
            continue
        fname = secure_filename(file.filename)
        dest  = os.path.join(PDF_DIR, fname)
        file.save(dest)
        uploaded.append(fname)
    return jsonify({"uploaded": uploaded, "errors": errors})


@app.route("/api/uploads/<filename>", methods=["DELETE"])
def delete_upload(filename: str):
    """Delete a file from PDFs/."""
    path = os.path.join(PDF_DIR, secure_filename(filename))
    if not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    os.remove(path)
    return jsonify({"deleted": filename})


@app.route("/api/outputs", methods=["GET"])
def list_outputs():
    """List all .md files in Outputs/."""
    files = []
    for f in sorted(os.listdir(OUTPUT_DIR)):
        if not f.endswith(".md"):
            continue
        path = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(path):
            files.append({
                "name": f,
                "size": os.path.getsize(path),
                "modified": datetime.datetime.fromtimestamp(
                    os.path.getmtime(path)
                ).strftime("%Y-%m-%d %H:%M"),
            })
    return jsonify(files)


@app.route("/api/outputs/<filename>", methods=["GET"])
def get_output(filename: str):
    """Download / view an output .md file."""
    name = os.path.basename(filename)
    return send_from_directory(OUTPUT_DIR, name)


@app.route("/api/outputs/<filename>", methods=["DELETE"])
def delete_output(filename: str):
    """Delete an output .md file."""
    path = safe_path(OUTPUT_DIR, filename)
    if not os.path.isfile(path):
        return jsonify({"error": "File not found"}), 404
    os.remove(path)
    return jsonify({"deleted": filename})


@app.route("/api/logs", methods=["GET"])
def list_logs():
    """List log files in Outputs/logs/."""
    files = []
    if os.path.isdir(LOG_DIR):
        for f in sorted(os.listdir(LOG_DIR), reverse=True)[:50]:
            path = os.path.join(LOG_DIR, f)
            if os.path.isfile(path):
                files.append({
                    "name": f,
                    "size": os.path.getsize(path),
                    "modified": datetime.datetime.fromtimestamp(
                        os.path.getmtime(path)
                    ).strftime("%Y-%m-%d %H:%M"),
                })
    return jsonify(files)


@app.route("/api/logs/<filename>", methods=["GET"])
def get_log(filename: str):
    """View a log file."""
    name = os.path.basename(filename)
    return send_from_directory(LOG_DIR, name)


@app.route("/api/run", methods=["POST"])
def run_conversion():
    """
    Start mdconver.py and stream its stdout via Server-Sent Events.
    Body JSON: { "files": ["fname1", "fname2"] }  — empty list means all files.
    """
    data  = request.get_json(force=True, silent=True) or {}
    files = data.get("files", [])  # list of basenames

    script = os.path.join(BASE_DIR, "mdconver.py")
    # -u = force unbuffered stdout so every print() appears immediately in the SSE stream
    cmd    = [sys.executable, "-u", script] + files
    env    = {**os.environ, "PYTHONUNBUFFERED": "1"}

    def generate():
        yield "data: Starting conversion…\n\n"
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            cwd=BASE_DIR,
        )
        for line in proc.stdout:
            line = line.rstrip("\n")
            # Escape SSE special characters
            escaped = line.replace("\n", " ")
            yield f"data: {escaped}\n\n"
        proc.wait()
        code = proc.returncode
        if code == 0:
            yield "data: ✅ Conversion complete.\n\n"
        else:
            yield f"data: ❌ Process exited with code {code}.\n\n"
        yield "data: __DONE__\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    print("=" * 60)
    print("  mdconver Web App — starting on http://localhost:4000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=4000, debug=False, threaded=True)
