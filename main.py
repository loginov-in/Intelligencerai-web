import config
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import timedelta

# Инцилизация Flask
app = Flask(__name__)
app.config.update(SECRET_KEY=config.SECRET_KEY)
app.permanent_session_lifetime = timedelta(days=365)


from endpoints.auth_login import *
from endpoints.mail_drowser import *
from endpoints.mail_drowser import *












if __name__ == "__main__":
    app.run(debug=True, port=9120)
