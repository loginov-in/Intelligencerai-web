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



# Секретный Ключ Flask #
SECRET_KEY = os.environ["SECRET_KEY"]
