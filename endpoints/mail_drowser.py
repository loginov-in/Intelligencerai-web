# Главная функция для отправки писем с кодом подтверждения использованием SMTP #
import hashlib
import os
import secrets
import smtplib
import string
from email.header import Header
from email.mime.text import MIMEText
from time import time

from flask import request, render_template, jsonify, session
from flask_login import login_required

from main import app

# Настройки SMTP сервера для отправки почты #
SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_EMAIL = os.environ["SMTP_EMAIL"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "False").lower() in ("true", "1", "t")
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "False").lower() in ("true", "1", "t")

SMTP_TIMEOUT = 10
RESEND_COOLDOWN_SECONDS = 60
CONFIRM_CODE_TTL_SECONDS = 600

# Хранилище ожидающих проверки кодов: email -> {"hash": ..., "expires_at": ...}
# Процессное: gunicorn должен работать с --workers 1
_pending_codes = {}


def _code_hash(email, code):
    return hashlib.sha256(f"{email}:{code}:{app.secret_key}".encode()).hexdigest()


# Функция для генерации случайного кода подтверждения #
def code_confirmation_email(length=6):
    # Оставляем только цифры '0123456789'
    return "".join(secrets.choice(string.digits) for _ in range(length))


# Отправка письма через SMTP #
def send_mail(to_email, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    if SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
    else:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=SMTP_TIMEOUT)
        if SMTP_USE_TLS:
            server.starttls()

    with server:
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [to_email], msg.as_string())


# --------------------------------------------- Frontend ------------------------------------ #
@app.route("/email_confirmation")
def email_confirmation():
    return render_template("email_confirmation.html")


# --------------------------------------------- Backend ------------------------------------ #
@app.route("/code/send_confirmation_email", methods=["POST"])
def send_confirmation_email():
    email = (request.form.get("email") or "").strip().lower()
    if not email or "@" not in email:
        return jsonify({"error": "Email is required"}), 400

    # Не чаще одного письма в минуту на сессию
    last_sent_at = session.get("confirmation_email_sent_at")
    if last_sent_at and time() - last_sent_at < RESEND_COOLDOWN_SECONDS:
        return jsonify({"error": "Код уже отправлен. Повторите попытку через минуту."}), 429

    confirmation_code = code_confirmation_email()

    try:
        send_mail(email, "Код подтверждения", f"Ваш код подтверждения: {confirmation_code}")
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    _pending_codes[email] = {
        "hash": _code_hash(email, confirmation_code),
        "expires_at": time() + CONFIRM_CODE_TTL_SECONDS,
    }
    session["confirmation_email_sent_at"] = time()
    return jsonify({"message": "Код подтверждения отправлен на ваш email"}), 200


@app.route("/code/verify_confirmation_email", methods=["POST"])
def verify_confirmation_email():
    email = (request.form.get("email") or "").strip().lower()
    code = (request.form.get("code") or "").strip()

    if not email or "@" not in email:
        return jsonify({"error": "Email is required"}), 400
    if not code.isdigit() or len(code) != 6:
        return jsonify({"error": "Код должен состоять из 6 цифр"}), 400

    entry = _pending_codes.get(email)
    if not entry or entry["expires_at"] < time():
        _pending_codes.pop(email, None)
        return jsonify({"error": "Код устарел. Запросите новый."}), 400

    if not secrets.compare_digest(entry["hash"], _code_hash(email, code)):
        return jsonify({"error": "Неверный код"}), 400

    _pending_codes.pop(email, None)
    session["confirmed_email"] = email
    return jsonify({"message": "Email подтвержден"}), 200
