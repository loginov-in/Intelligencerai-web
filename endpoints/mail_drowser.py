# Главная функция для отправки писем с кодом подтверждения использованием SMTP #
import hashlib
import os
import secrets
import smtplib
import string
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from time import time

from flask import url_for
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


# Логотип IntelligencerAI для письма: SVG перекрашиваем в чёрный, т.к. исходный белый
_LOGO_SVG_PATH = Path(__file__).resolve().parent.parent / "static" / "img" / "logo.svg"


def _brand_logo_svg():
    try:
        svg = _LOGO_SVG_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""
    svg = svg.replace('fill="white"', 'fill="#111111"')
    return svg.replace("<svg ", '<svg style="display:block;width:100%;height:auto;border:0;" ', 1)


def _site_link(endpoint):
    try:
        return url_for(endpoint, _external=True)
    except Exception:
        pass
    try:
        return url_for(endpoint)
    except Exception:
        return "#"


# Письмо-карточка: крупный код подтверждения и всё #
def code_email_html(code, minutes=10):
    template = app.jinja_env.get_template("email_verification.html")
    return template.render(
        verification_code=code,
        minutes=minutes,
        logo_svg=_brand_logo_svg(),
        home_url=_site_link("login"),
        docs_url=_site_link("docs"),
    )


# Отправка письма через SMTP #
def send_mail(to_email, subject, body, html=None):
    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
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


def send_code_email(to_email, code, subject="Код подтверждения"):
    minutes = max(1, CONFIRM_CODE_TTL_SECONDS // 60)
    send_mail(
        to_email,
        subject,
        f"Ваш код подтверждения: {code}. Код действует {minutes} минут.",
        html=code_email_html(code, minutes),
    )
