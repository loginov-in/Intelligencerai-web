import secrets
from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

import config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

ROLES = ("director", "deputy", "admin", "content_manager")
ROLE_LABELS = {
    "director": "Директор",
    "deputy": "Заместитель директора",
    "admin": "Администратор",
    "content_manager": "Контент-менеджер",
}
TWO_FACTOR_METHODS = ("none", "email", "totp")


class User(db.Model, UserMixin):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), nullable=False)
    lastname = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=True, nullable=False)
    avatar_path = db.Column(db.String(255))
    two_factor_method = db.Column(db.String(10), default="none", nullable=False)
    totp_secret = db.Column(db.String(64))
    active_org_id = db.Column(db.Integer, db.ForeignKey("organization.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship(
        "Membership", back_populates="user", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def organization(self):
        if self.active_org_id:
            for m in self.memberships:
                if m.org_id == self.active_org_id:
                    return m.organization
        return self.memberships[0].organization if self.memberships else None

    @property
    def role(self):
        org = self.organization
        if not org:
            return None
        for m in self.memberships:
            if m.org_id == org.id:
                return m.role
        return None

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, "")


class Organization(db.Model):
    __tablename__ = "organization"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    category = db.Column(db.String(60), nullable=False, default="Школа")
    invite_token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(16))
    avatar_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship("Membership", back_populates="organization", lazy="selectin")
    files = db.relationship("FileRecord", back_populates="organization", lazy="dynamic")


class Membership(db.Model):
    __tablename__ = "membership"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="content_manager")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="memberships")
    organization = db.relationship("Organization", back_populates="members")

    __table_args__ = (db.UniqueConstraint("user_id", "org_id", name="uq_membership_user_org"),)


class FileRecord(db.Model):
    __tablename__ = "file_record"

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    size = db.Column(db.BigInteger, nullable=False, default=0)
    mime = db.Column(db.String(120))
    kind = db.Column(db.String(20), nullable=False, default="file")
    share_token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(12))
    owner_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    org_id = db.Column(db.Integer, db.ForeignKey("organization.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User")
    organization = db.relationship("Organization", back_populates="files")


def init_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql+psycopg2://{config.POSTGRESQL_USER}:{config.POSTGRESQL_PASSWORD}"
        f"@{config.POSTGRESQL_HOST}:{config.POSTGRESQL_PORT}/{config.POSTGRESQL_DBNAME}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    with app.app_context():
        db.create_all()
