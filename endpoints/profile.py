import base64
import os
import secrets
from time import time

from flask import jsonify, request, session
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from endpoints import mail_drowser as mailer
from main import app
from db_drowser import User, bcrypt, db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVATAR_DIR = os.path.join(BASE_DIR, "static", "uploads", "avatars")
MAX_AVATAR_SIZE = 2 * 1024 * 1024
AVATAR_EXTS = {"png", "jpg", "jpeg", "webp", "gif"}


# -----------------------------------   Профиль   -----------------------------------
@app.route("/api/profile", methods=["POST"])
@login_required
def update_profile():
    data = request.get_json(silent=True) or request.form
    name = (data.get("name") or "").strip()
    lastname = (data.get("lastname") or "").strip()
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()

    errors = {}
    if not name or len(name) > 30:
        errors["name"] = "Укажите имя (до 30 символов)"
    if not lastname or len(lastname) > 30:
        errors["lastname"] = "Укажите фамилию (до 30 символов)"
    if not username or len(username) > 50 or " " in username:
        errors["username"] = "Укажите имя пользователя без пробелов"
    if not email or "@" not in email:
        errors["email"] = "Укажите корректную почту"

    if not errors:
        clash = User.query.filter(
            User.id != current_user.id, db.func.lower(User.username) == username.lower()
        ).first()
        if clash:
            errors["username"] = "Имя пользователя занято"
        clash = User.query.filter(User.id != current_user.id, User.email == email).first()
        if clash:
            errors["email"] = "Почта уже используется"

    if errors:
        return jsonify({"errors": errors}), 400

    current_user.name = name
    current_user.lastname = lastname
    current_user.username = username
    current_user.email = email
    db.session.commit()
    return jsonify({"message": "Профиль обновлён", "user": {
        "name": current_user.name,
        "lastname": current_user.lastname,
        "username": current_user.username,
        "email": current_user.email,
    }}), 200


@app.route("/api/password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json(silent=True) or request.form
    current = data.get("current") or ""
    new = data.get("new") or ""
    confirm = data.get("confirm") or ""

    if not bcrypt.check_password_hash(current_user.password_hash, current):
        return jsonify({"errors": {"current": "Текущий пароль неверен"}}), 400
    if len(new) < 8:
        return jsonify({"errors": {"new": "Минимум 8 символов"}}), 400
    if new != confirm:
        return jsonify({"errors": {"confirm": "Пароли не совпадают"}}), 400

    current_user.password_hash = bcrypt.generate_password_hash(new).decode()
    db.session.commit()
    return jsonify({"message": "Пароль изменён"}), 200


@app.route("/api/avatar", methods=["POST"])
@login_required
def upload_avatar():
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

    os.makedirs(AVATAR_DIR, exist_ok=True)
    filename = f"user_{current_user.id}_{int(time())}.{ext}"
    upload.save(os.path.join(AVATAR_DIR, filename))
    current_user.avatar_path = f"/static/uploads/avatars/{filename}"
    db.session.commit()
    return jsonify({"message": "Аватар обновлён", "avatar": current_user.avatar_path}), 200


# -----------------------------------   2FA   -----------------------------------
def _user_code_entry_ok(user, code):
    entry = mailer._pending_codes.get(user.email)
    if not entry or entry["expires_at"] < time():
        return False
    return secrets.compare_digest(entry["hash"], mailer._code_hash(user.email, code))


@app.route("/api/2fa", methods=["POST"])
@login_required
def set_two_factor():
    data = request.get_json(silent=True) or request.form
    method = data.get("method") or "none"

    if method == "none":
        current_user.two_factor_method = "none"
        current_user.totp_secret = None
        session.pop("totp_pending_secret", None)
        db.session.commit()
        return jsonify({"message": "Двухэтапная защита отключена", "method": "none"}), 200

    if method == "email":
        current_user.two_factor_method = "email"
        current_user.totp_secret = None
        session.pop("totp_pending_secret", None)
        db.session.commit()
        return jsonify({"message": "Код на почту включён", "method": "email"}), 200

    if method == "totp":
        import pyotp

        secret = session.get("totp_pending_secret") or pyotp.random_base32()
        session["totp_pending_secret"] = secret
        uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=current_user.email, issuer_name="IntelligencerAI"
        )
        import qrcode

        img = qrcode.make(uri)
        buf = getattr(img, "buffer", None)
        if buf is None:
            from io import BytesIO

            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
        qr_b64 = base64.b64encode(buf.read()).decode()
        return jsonify({
            "message": "Подтвердите код из приложения",
            "method": "totp",
            "qr": f"data:image/png;base64,{qr_b64}",
            "secret": secret,
        }), 200

    return jsonify({"error": "Неизвестный метод"}), 400


@app.route("/api/2fa/send_code", methods=["POST"])
@login_required
def send_two_factor_code():
    last_sent_at = session.get("confirmation_email_sent_at")
    if last_sent_at and time() - last_sent_at < mailer.RESEND_COOLDOWN_SECONDS:
        return jsonify({"error": "Код уже отправлен. Повторите попытку через минуту."}), 429
    try:
        code = mailer.code_confirmation_email()
        mailer.send_code_email(current_user.email, code)
        mailer._pending_codes[current_user.email] = {
            "hash": mailer._code_hash(current_user.email, code),
            "expires_at": time() + mailer.CONFIRM_CODE_TTL_SECONDS,
        }
        session["confirmation_email_sent_at"] = time()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify({"message": "Код отправлен"}), 200


@app.route("/api/2fa/verify", methods=["POST"])
@login_required
def verify_two_factor():
    data = request.get_json(silent=True) or request.form
    code = (data.get("code") or "").strip()
    pending = session.get("totp_pending_secret")

    if pending:
        import pyotp

        if not pyotp.TOTP(pending).verify(code, valid_window=1):
            return jsonify({"error": "Неверный код"}), 400
        current_user.totp_secret = pending
        current_user.two_factor_method = "totp"
        session.pop("totp_pending_secret", None)
        db.session.commit()
        return jsonify({"message": "Google Authenticator подключён", "method": "totp"}), 200

    if current_user.two_factor_method == "email":
        if not _user_code_entry_ok(current_user, code):
            return jsonify({"error": "Неверный код"}), 400
        mailer._pending_codes.pop(current_user.email, None)
        return jsonify({"message": "Почта подтверждена", "method": "email"}), 200

    return jsonify({"error": "Сначала выберите метод"}), 400
