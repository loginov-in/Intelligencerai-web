import smtplib
import secrets
import requests
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.header import Header
from main import *
from flask import Flask, request, send_file, render_template, redirect, abort, session, url_for, make_response, jsonify
from sqlalchemy import func, and_
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt


#Контроль доступа
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    class User:
         ...

    return User.query.get(int(user_id))






# Допустимый код приглашения для регистрации аккунта (проверка на бекенде)
ACTIVATE_INVITE_CODE = 'ТЕСТОВЫЙ'

#-----------------------------------   FRONTEND   -----------------------------------

@app.route("/")
def login():
    return render_template("login.html")


@app.route("/registr", methods=["GET", "POST"])
def registr():
    if request.method == "POST":
        return render_template("create_account.html", form=request.form, errors={})

    return render_template("create_account.html")

@app.route("/signup")
def signup():
    return redirect(url_for("registr"))


@app.route("/forgot_password")
def forgot_password():
    return redirect(url_for("login"))


@app.route("/apps")
@login_required
def apps():
    if not current_user.is_confirmed: return render_template('not_confirmed.html')

    return render_template("apps.html",user=current_user)






#-----------------------------------   Backend   -----------------------------------
@app.route("/api/creete_profile", methods=["GET", "POST"])
def create_api_profile():
       pass
            