import os
import re
import secrets
from main import app, config, psycopg2, SQLAlchemy, Bcrypt, UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime
from sqlalchemy.orm import deferred
from sqlalchemy import UUID, text


# ---- Инцилизация БД ---- #
POSTGRESQL_HOST = os.environ["POSTGRESQL_HOST"]
POSTGRESQL_PORT = os.environ["POSTGRESQL_PORT"]
POSTGRESQL_USER = os.environ["POSTGRESQL_USER"]
POSTGRESQL_DBNAME = os.environ["POSTGRESQL_DBNAME"]
POSTGRESQL_PASSWORD = os.environ["POSTGRESQL_PASSWORD"]


app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{POSTGRESQL_USER}:{POSTGRESQL_PASSWORD}@{POSTGRESQL_HOST}:{POSTGRESQL_PORT}/{POSTGRESQL_DBNAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)



# -------------------------- all Accounts -------------------------- #
class accounts(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

    def get_id(self):
        return f"accounts-{self.id}"

