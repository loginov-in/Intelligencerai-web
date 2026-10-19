import os
import secrets
from time import time

from flask import jsonify, redirect, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from main import app
from db_drowser import Membership, Organization, ROLE_LABELS, User, db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORG_AVATAR_DIR = os.path.join(BASE_DIR, "static", "uploads", "orgs")
MAX_AVATAR_SIZE = 2 * 1024 * 1024
AVATAR_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}
EDIT_ROLES = ("director", "deputy", "admin")


def _can_edit_org(user):
    return user.role in EDIT_ROLES


def _org_json(org, invite_url):
    members = []
    for m in Membership.query.filter(Membership.org_id == org.id).order_by(Membership.id).all():
        u = m.user
        if not u:
            continue
        members.append({
            "id": u.id,
            "name": u.name,
            "lastname": u.lastname,
            "username": u.username,
            "role": m.role,
            "role_label": ROLE_LABELS.get(m.role, m.role),
            "avatar": u.avatar_path,
        })
    return {
        "id": org.id,
        "name": org.name,
        "category": org.category,
        "avatar": org.avatar_path,
        "invite_url": invite_url,
        "members": members,
        "my_role": current_user.role,
        "my_role_label": ROLE_LABELS.get(current_user.role, ""),
        "can_edit": _can_edit_org(current_user),
    }


@app.route("/api/org")
@login_required
def get_org():
    org = current_user.organization
    if not org:
        return jsonify({"error": "Организация не найдена"}), 404
    invite_url = request.host_url.rstrip("/") + url_for("join_org", token=org.invite_token)
    return jsonify(_org_json(org, invite_url)), 200


@app.route("/api/org", methods=["POST"])
@login_required
def update_org():
    org = current_user.organization
    if not org:
        return jsonify({"error": "Организация не найдена"}), 404
    if not _can_edit_org(current_user):
        return jsonify({"error": "Недостаточно прав"}), 403

    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()

    if not name or len(name) > 120:
        return jsonify({"errors": {"name": "Укажите название (до 120 символов)"}}), 400
    clash = Organization.query.filter(
        Organization.id != org.id, db.func.lower(Organization.name) == name.lower()
    ).first()
    if clash:
        return jsonify({"errors": {"name": "Такая организация уже есть в системе"}}), 400
    if not category or len(category) > 60:
        category = org.category

    org.name = name
    org.category = category
    db.session.commit()
    invite_url = request.host_url.rstrip("/") + url_for("join_org", token=org.invite_token)
    return jsonify({"message": "Организация обновлена", "org": _org_json(org, invite_url)}), 200


@app.route("/api/org/avatar", methods=["POST"])
@login_required
def org_avatar():
    org = current_user.organization
    if not org:
        return jsonify({"error": "Организация не найдена"}), 404
    if not _can_edit_org(current_user):
        return jsonify({"error": "Недостаточно прав"}), 403

    upload = request.files.get("avatar")
    if not upload or not upload.filename:
        return jsonify({"error": "Файл не выбран"}), 400
    ext = (upload.filename.rsplit(".", 1)[-1] or "").lower()
    if ext not in AVATAR_EXTS:
        return jsonify({"error": "Допустимы png, jpg, jpeg, webp, gif"}), 400

    upload.stream.seek(0, os.SEEK_END)
    size = upload.stream.tell()
    upload.stream.seek(0)
    if size > MAX_AVATAR_SIZE:
        return jsonify({"error": "Аватар больше 2 МБ"}), 413

    os.makedirs(ORG_AVATAR_DIR, exist_ok=True)
    filename = f"org_{org.id}_{int(time())}.{ext}"
    upload.save(os.path.join(ORG_AVATAR_DIR, filename))
    org.avatar_path = f"/static/uploads/orgs/{filename}"
    db.session.commit()
    return jsonify({"message": "Аватар обновлён", "avatar": org.avatar_path}), 200


@app.route("/api/org/invite/regenerate", methods=["POST"])
@login_required
def regenerate_invite():
    org = current_user.organization
    if not org:
        return jsonify({"error": "Организация не найдена"}), 404
    if not _can_edit_org(current_user):
        return jsonify({"error": "Недостаточно прав"}), 403
    org.invite_token = secrets.token_urlsafe(16)
    db.session.commit()
    invite_url = request.host_url.rstrip("/") + url_for("join_org", token=org.invite_token)
    return jsonify({"message": "Ссылка обновлена", "invite_url": invite_url}), 200


@app.route("/join/<token>")
@login_required
def join_org(token):
    org = Organization.query.filter(Organization.invite_token == token).first()
    if not org:
        return jsonify({"error": "Ссылка-приглашение недействительна"}), 404

    existing = Membership.query.filter(
        Membership.user_id == current_user.id, Membership.org_id == org.id
    ).first()
    if not existing:
        db.session.add(Membership(user_id=current_user.id, org_id=org.id, role="content_manager"))
    current_user.active_org_id = org.id
    db.session.commit()
    return redirect(url_for("organization"))
