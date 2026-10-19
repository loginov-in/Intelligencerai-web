import config
from datetime import timedelta
from flask import Flask
from db_drowser import init_db, login_manager, db, bcrypt

app = Flask(__name__)
app.config.update(SECRET_KEY=config.SECRET_KEY)
app.permanent_session_lifetime = timedelta(days=365)

init_db(app)

from endpoints.auth_login import *  
from endpoints.mail_drowser import *  
from endpoints.files import *  
from endpoints.profile import *  
from endpoints.organization import *  


if __name__ == "__main__":
    app.run(debug=True, port=9120)
