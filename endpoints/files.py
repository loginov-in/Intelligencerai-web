import os
import tempfile
import zipfile
from datetime import datetime

from flask import (
    abort,
    jsonify,
    render_template,
    request,
    send_file,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from main import app
from db_drowser import FileRecord, Organization, db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_ROOT = os.path.join(BASE_DIR, "uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 МБ (nginx client_max_body_size 10m)
ALLOWED_KINDS = ("file", "brandbook")


def _org_of_user():
    return current_user.organization


def _file_to_dict(f):
    return {
        "id": f.id,
        "name": f.original_name,
        "size": f.size,
        "mime": f.mime,
        "kind": f.kind,
        "created_at": f.created_at.strftime("%d.%m.%Y %H:%M") if f.created_at else "",
        "owner": f"{f.owner.name} {f.owner.lastname}" if f.owner else "—",
        "download_url": f"/files/{f.id}/download",
        "share_url": f"/f/{f.share_token}",
    }


@app.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    org = _org_of_user()
    if not org:
        return jsonify({"error": "У вас нет организации"}), 400

    upload = request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"error": "Файл не выбран"}), 400

    kind = request.form.get("kind", "file")
    if kind not in ALLOWED_KINDS:
        kind = "file"

    upload.stream.seek(0, os.SEEK_END)
    size = upload.stream.tell()
    upload.stream.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"error": "Файл больше 10 МБ"}), 413

    original = secure_filename(upload.filename) or "file"
    folder = os.path.join(UPLOAD_ROOT, f"org_{org.id}")
    os.makedirs(folder, exist_ok=True)
    stored = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{original}"
    path = os.path.join(folder, stored)
    upload.save(path)

    record = FileRecord(
        original_name=upload.filename,
        stored_path=path,
        size=size,
        mime=upload.mimetype,
        kind=kind,
        owner_id=current_user.id,
        org_id=org.id,
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(_file_to_dict(record)), 201


@app.route("/api/files")
@login_required
def list_files():
    org = _org_of_user()
    if not org:
        return jsonify({"files": []}), 200

    kind = request.args.get("kind")
    query = FileRecord.query.filter(FileRecord.org_id == org.id)
    if kind in ALLOWED_KINDS:
        query = query.filter(FileRecord.kind == kind)
    files = query.order_by(FileRecord.created_at.desc()).limit(100).all()
    return jsonify({"files": [_file_to_dict(f) for f in files]}), 200


@app.route("/files/<int:file_id>/download")
@login_required
def download_file(file_id):
    record = db.session.get(FileRecord, file_id)
    if not record:
        abort(404)
    org = _org_of_user()
    if not org or record.org_id != org.id:
        abort(403)
    if not os.path.exists(record.stored_path):
        abort(404)
    return send_file(record.stored_path, as_attachment=True, download_name=record.original_name)


@app.route("/api/backup")
@login_required
def backup_files():
    org = _org_of_user()
    if not org:
        return jsonify({"error": "У вас нет организации"}), 400

    files = FileRecord.query.filter(FileRecord.org_id == org.id).order_by(FileRecord.created_at).all()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    used = set()
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if not os.path.exists(f.stored_path):
                continue
            name = f.original_name
            if name in used:
                base, ext = os.path.splitext(name)
                name = f"{base}_{f.id}{ext}"
            used.add(name)
            zf.write(f.stored_path, arcname=name)
    tmp.close()
    return send_file(
        tmp.name,
        as_attachment=True,
        download_name=f"backup_{org.name}_{datetime.utcnow().strftime('%Y%m%d')}.zip",
    )


@app.route("/f/<token>")
def share_page(token):
    record = FileRecord.query.filter(FileRecord.share_token == token).first_or_404()
    return render_template("share.html", file=record)


@app.route("/f/<token>/download")
def share_download(token):
    record = FileRecord.query.filter(FileRecord.share_token == token).first_or_404()
    if not os.path.exists(record.stored_path):
        abort(404)
    return send_file(record.stored_path, as_attachment=True, download_name=record.original_name)
