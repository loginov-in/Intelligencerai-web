# QR-вход: одноразовая ссылка с токеном #
# Доверенное устройство создаёт QR в настройках; открытие ссылки
# (скан камерой) сразу авторизует аккаунт на новом устройстве без пароля.
import base64
import secrets
from io import BytesIO
from time import time

import qrcode
from flask import Response, jsonify, redirect, url_for
from flask_login import current_user, login_required, login_user

from db_drowser import User, db
from main import app

QR_TOKEN_TTL_SECONDS = 300

# Хранилище активных токенов: token -> {"user_id": ..., "expires_at": ...}
# Процессное: gunicorn должен работать с --workers 1 (как у кодов подтверждения)
_qr_tokens = {}


def _prune_expired():
    now = time()
    for token in [t for t, entry in _qr_tokens.items() if entry["expires_at"] <= now]:
        _qr_tokens.pop(token, None)


def _consume_url(token):
    try:
        return url_for("qr_login_consume", token=token, _external=True)
    except Exception:
        pass
    try:
        return url_for("qr_login_consume", token=token)
    except Exception:
        return ""


def _qr_png_data_uri(url):
    img = qrcode.make(url)
    buf = getattr(img, "buffer", None)
    if buf is None:
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode()


_INVALID_HTML = """<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ссылка недействительна · IntelligencerAI</title>
</head>
<body style="margin:0;padding:48px 24px;font-family:Arial,Helvetica,sans-serif;background:#ffffff;color:#333333;">
  <p style="font-size:22px;font-weight:bold;margin:0 0 10px;">Ссылка недействительна или устарела</p>
  <p style="font-size:15px;color:#666666;margin:0 0 20px;line-height:1.5;">
    QR-код действует 5 минут и только один раз.<br>Создайте новый код в настройках аккаунта.
  </p>
  <a href="{login_url}" style="font-size:15px;color:#111111;">Перейти ко входу</a>
</body>
</html>"""


@app.route("/api/qr-login", methods=["POST"])
@login_required
def create_qr_login():
    _prune_expired()

    # Одновременно действует только один QR-код на пользователя
    for token, entry in list(_qr_tokens.items()):
        if entry["user_id"] == current_user.id:
            _qr_tokens.pop(token, None)

    token = secrets.token_urlsafe(32)
    _qr_tokens[token] = {"user_id": current_user.id, "expires_at": time() + QR_TOKEN_TTL_SECONDS}

    url = _consume_url(token)
    if not url:
        _qr_tokens.pop(token, None)
        return jsonify({"error": "Не удалось построить ссылку для входа"}), 500

    return jsonify({
        "url": url,
        "qr": _qr_png_data_uri(url),
        "expires_in": QR_TOKEN_TTL_SECONDS,
    }), 200


@app.route("/qr_login/<token>")
def qr_login_consume(token):
    _prune_expired()
    entry = _qr_tokens.pop(token, None)
    if not entry:
        return Response(
            _INVALID_HTML.format(login_url=url_for("login")),
            mimetype="text/html",
        )

    user = db.session.get(User, entry["user_id"])
    if not user:
        return Response(
            _INVALID_HTML.format(login_url=url_for("login")),
            mimetype="text/html",
        )

    login_user(user)
    return redirect(url_for("apps"))
