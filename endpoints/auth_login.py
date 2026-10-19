import re
import secrets
from time import time

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from endpoints import mail_drowser as mailer
from main import app
from db_drowser import Membership, Organization, ROLE_LABELS, User, bcrypt, db, login_manager

# Хранилище ожидающих создания аккаунтов: email -> {...} (процессное, workers=1)
_pending_registrations = {}
REGISTRATION_TTL_SECONDS = 600

# Допустимый код приглашения для регистрации аккаунта (проверка на бекенде)
ACTIVATE_INVITE_CODE = 'ТЕСТОВЫЙ'


@login_manager.user_loader
def load_user(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


# -----------------------------------   Валидация   -----------------------------------
def _validate_registration(form):
    errors = {}
    name = (form.get("name") or "").strip()
    lastname = (form.get("lastname") or "").strip()
    organization = (form.get("organization") or "").strip()
    email = (form.get("email") or "").strip().lower()
    username = (form.get("username") or "").strip()
    password = form.get("password") or ""
    confirm = form.get("confirm") or ""

    if not name or len(name) > 30:
        errors["name"] = "Укажите имя (до 30 символов)"
    if not lastname or len(lastname) > 30:
        errors["lastname"] = "Укажите фамилию (до 30 символов)"
    if not organization or len(organization) > 120:
        errors["organization"] = "Укажите название организации"
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        errors["email"] = "Укажите корректную почту"
    if not re.fullmatch(r"[A-Za-z0-9_.]{3,50}", username):
        errors["username"] = "3–50 символов: латиница, цифры, _ и ."
    if not password:
        errors["password"] = "Введите пароль"
    elif len(password) < 8:
        errors["password"] = "Минимум 8 символов"
    elif password != confirm:
        errors["confirm"] = "Пароли не совпадают"

    if not errors:
        if User.query.filter(db.func.lower(User.username) == username.lower()).first():
            errors["username"] = "Такое имя пользователя уже занято"
        if User.query.filter(User.email == email).first():
            errors["email"] = "Такая почта уже зарегистрирована"
        if Organization.query.filter(db.func.lower(Organization.name) == organization.lower()).first():
            errors["organization"] = "Такая организация уже есть в системе"
        if User.query.filter(
            db.func.lower(User.name) == name.lower(),
            db.func.lower(User.lastname) == lastname.lower()
        ).first():
            errors["lastname"] = "Пользователь с таким именем и фамилией уже есть"

    if errors:
        return errors, {}

    return {}, {
        "name": name,
        "lastname": lastname,
        "organization": organization,
        "email": email,
        "username": username,
        "password_hash": bcrypt.generate_password_hash(password).decode(),
    }


def _issue_email_code(email):
    code = mailer.code_confirmation_email()
    mailer.send_code_email(email, code)
    mailer._pending_codes[email] = {
        "hash": mailer._code_hash(email, code),
        "expires_at": time() + mailer.CONFIRM_CODE_TTL_SECONDS,
    }
    session["confirmation_email_sent_at"] = time()


# -----------------------------------   FRONTEND   -----------------------------------
@app.route("/")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("apps"))
    return render_template("login.html", errors={}, form={})


@app.route("/", methods=["POST"])
def login_post():
    identifier = (request.form.get("identifier") or request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    remember = bool(request.form.get("remember"))

    user = None
    if identifier:
        user = User.query.filter(
            db.or_(db.func.lower(User.username) == identifier, db.func.lower(User.email) == identifier)
        ).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return render_template(
            "login.html",
            errors={"form": "Неверное имя пользователя или пароль"},
            form={"identifier": request.form.get("identifier", "")},
        ), 401

    method = user.two_factor_method or "none"
    if method == "email":
        try:
            _issue_email_code(user.email)
        except Exception:
            return render_template(
                "login.html",
                errors={"form": "Не удалось отправить код на почту. Попробуйте позже."},
                form={"identifier": request.form.get("identifier", "")},
            ), 502
        session["2fa_user_id"] = user.id
        session["2fa_remember"] = remember
        return redirect(url_for("two_factor"))
    if method == "totp" and user.totp_secret:
        session["2fa_user_id"] = user.id
        session["2fa_remember"] = remember
        return redirect(url_for("two_factor"))

    login_user(user, remember=remember)
    return redirect(request.args.get("next") or url_for("apps"))


@app.route("/two_factor")
def two_factor():
    uid = session.get("2fa_user_id")
    if not uid:
        return redirect(url_for("login"))
    user = db.session.get(User, uid)
    if not user:
        return redirect(url_for("login"))
    return render_template("two_factor.html", method=user.two_factor_method)


@app.route("/two_factor/verify", methods=["POST"])
def two_factor_verify():
    uid = session.get("2fa_user_id")
    user = db.session.get(User, uid) if uid else None
    if not user:
        return redirect(url_for("login"))

    code = (request.form.get("code") or "").strip()
    ok = False

    if user.two_factor_method == "email":
        entry = mailer._pending_codes.get(user.email)
        if entry and entry["expires_at"] >= time() and secrets.compare_digest(
            entry["hash"], mailer._code_hash(user.email, code)
        ):
            mailer._pending_codes.pop(user.email, None)
            ok = True
    elif user.two_factor_method == "totp" and user.totp_secret:
        import pyotp

        ok = pyotp.TOTP(user.totp_secret).verify(code, valid_window=1)

    if not ok:
        return render_template("two_factor.html", method=user.two_factor_method, error="Неверный код"), 401

    session.pop("2fa_user_id", None)
    remember = bool(session.pop("2fa_remember", False))
    login_user(user, remember=remember)
    return redirect(url_for("apps"))


@app.route("/registr", methods=["GET", "POST"])
def registr():
    if request.method == "GET":
        return render_template("create_account.html", errors={}, form={}, step="form")

    errors, data = _validate_registration(request.form)
    if errors:
        return render_template(
            "create_account.html", errors=errors, form=request.form, step="form"
        ), 400

    _pending_registrations[data["email"]] = {
        **data,
        "expires_at": time() + REGISTRATION_TTL_SECONDS,
    }
    for email in [e for e, v in _pending_registrations.items() if v["expires_at"] < time()]:
        _pending_registrations.pop(email, None)

    try:
        _issue_email_code(data["email"])
    except Exception as exc:
        _pending_registrations.pop(data["email"], None)
        return render_template(
            "create_account.html",
            errors={"email": f"Не удалось отправить код: {exc}"},
            form=request.form,
            step="form",
        ), 502

    return render_template(
        "create_account.html",
        errors={},
        form={},
        step="code",
        email=data["email"],
    )


@app.route("/registr/resend", methods=["POST"])
def registr_resend():
    email = (request.form.get("email") or "").strip().lower()
    if email not in _pending_registrations:
        return jsonify({"error": "Сессия регистрации истекла. Начните заново."}), 400

    last_sent_at = session.get("confirmation_email_sent_at")
    if last_sent_at and time() - last_sent_at < mailer.RESEND_COOLDOWN_SECONDS:
        return jsonify({"error": "Код уже отправлен. Повторите попытку через минуту."}), 429

    try:
        _issue_email_code(email)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502
    return jsonify({"message": "Код отправлен"}), 200


@app.route("/registr/confirm", methods=["POST"])
def registr_confirm():
    email = (request.form.get("email") or "").strip().lower()
    code = (request.form.get("code") or "").strip()

    pending = _pending_registrations.get(email)
    if not pending or pending["expires_at"] < time():
        _pending_registrations.pop(email, None)
        return render_template(
            "create_account.html",
            errors={"code": "Сессия регистрации истекла. Начните заново."},
            form={},
            step="form",
        ), 400

    entry = mailer._pending_codes.get(email)
    if not entry or entry["expires_at"] < time():
        mailer._pending_codes.pop(email, None)
        return render_template(
            "create_account.html",
            errors={"code": "Код устарел. Запросите новый."},
            form={},
            step="code",
            email=email,
        ), 400
    if not code.isdigit() or len(code) != 6 or not secrets.compare_digest(
        entry["hash"], mailer._code_hash(email, code)
    ):
        return render_template(
            "create_account.html",
            errors={"code": "Неверный код"},
            form={},
            step="code",
            email=email,
        ), 400

    if User.query.filter(User.email == email).first():
        _pending_registrations.pop(email, None)
        return redirect(url_for("login"))

    user = User(
        name=pending["name"],
        lastname=pending["lastname"],
        username=pending["username"],
        email=email,
        password_hash=pending["password_hash"],
        is_confirmed=True,
    )
    org = Organization(name=pending["organization"], category="Школа")
    db.session.add(user)
    db.session.add(org)
    db.session.flush()
    db.session.add(Membership(user_id=user.id, org_id=org.id, role="director"))
    user.active_org_id = org.id
    db.session.commit()

    _pending_registrations.pop(email, None)
    mailer._pending_codes.pop(email, None)
    login_user(user)
    return redirect(url_for("apps"))


@app.route("/signup")
def signup():
    return redirect(url_for("registr"))


@app.route("/forgot_password")
def forgot_password():
    return redirect(url_for("login"))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/apps")
@login_required
def apps():
    if not current_user.is_confirmed:
        return render_template("not_confirmed.html")
    return render_template("apps.html", user=current_user)


@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html", user=current_user)


@app.route("/organization")
@login_required
def organization():
    return render_template("organization.html", user=current_user)





@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/api/creete_profile", methods=["GET", "POST"])
def create_api_profile():
    return jsonify({"error": "Not implemented"}), 501
