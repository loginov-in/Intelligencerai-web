import os
from dotenv import load_dotenv

load_dotenv()


# --- База данных ---
# os.environ[...] выбросит ошибку, если переменная не найдена,
# что предотвратит запуск с неполной конфигурацией.
POSTGRESQL_HOST = os.environ["POSTGRESQL_HOST"]
POSTGRESQL_PORT = os.environ["POSTGRESQL_PORT"]
POSTGRESQL_USER = os.environ["POSTGRESQL_USER"]
POSTGRESQL_DBNAME = os.environ["POSTGRESQL_DBNAME"]
POSTGRESQL_PASSWORD = os.environ["POSTGRESQL_PASSWORD"]



# --- S3 / Object Storage ---
S3_URL = os.environ["S3_URL"]
S3_BUCKET = os.environ["baget_name"]
S3_ACCESS_KEY = os.environ["S3_Access_Key"]
S3_SECRET_ACCESS_KEY = os.environ["S3_Secret_Access_Key"]
S3_REGION = os.environ["reguon"]


# Секретный Ключ Flask #
SECRET_KEY = os.environ["SECRET_KEY"]



# --- SMTP настройки для отправки почты --- #
SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_EMAIL = os.environ["SMTP_EMAIL"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "False").lower() in ("true", "1", "t")
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "False").lower() in ("true", "1", "t")