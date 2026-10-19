# Главная функция для отправки писем с кодом подтверждения использованием SMTP #
import hashlib
import os
import secrets
import smtplib
import string
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import time

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


# Письмо-карточка: крупный код подтверждения и всё #
def code_email_html(code, minutes=10):
    return f"""<!doctype html>
<html lang="ru">
<body style="margin:0;padding:32px 16px;background:#f4f2fb;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="max-width:420px;border-collapse:collapse;background:#ffffff;border-radius:20px;padding:32px;">
          <tr>
            <td align="center" style="padding:0 0 8px;font-size:18px;font-weight:bold;color:#2b2440;">
              IntelligencerAI
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:0 0 24px;font-size:14px;color:#6b6480;">
              Код подтверждения
            </td>
          </tr>
          <tr>
            <td align="center"
                style="padding:18px 12px;background:#f4f2fb;border-radius:14px;font-size:34px;font-weight:bold;
                       letter-spacing:8px;color:#2b2440;font-family:Consolas,Menlo,monospace;">
              {code}
            </td>
          </tr>
          <tr>
            <td align="center" style="padding:24px 0 0;font-size:12px;color:#8b8499;">
              Код действует {minutes} минут. Если вы не запрашивали код, просто проигнорируйте письмо.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


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
