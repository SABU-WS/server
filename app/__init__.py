from config import *
from app.utils.db_mgmt import database_allowed

from flask import Flask
from flask_login import (
	UserMixin,
	login_user,
	LoginManager,
	login_required,
	logout_user,
	current_user,
)
from flask_socketio import (
	SocketIO,
	emit,
	disconnect,
)
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy 
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_wtf.csrf import CSRFProtect, CSRFError
from werkzeug.middleware.proxy_fix import ProxyFix

import datetime
import logging
import string
import random
import os
import re
import uuid

log_format = "%(levelname)s [%(asctime)s] %(name)s  %(message)s"
logging.basicConfig(format=log_format,level=logging.INFO,filename="/sabu/logs/server/sabu.log",filemode="a")
logger = logging.getLogger("sabu.server")

app = Flask(__name__)
app.config["SECRET_KEY"] = "".join(
	random.choices(string.ascii_letters + string.digits, k=30)
)
app.config["SQLALCHEMY_DATABASE_URI"] = database_allowed()
app.config["UPLOAD_FOLDER"] = ROOT_PATH
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
app.config["SESSION_TYPE"] = 'filesystem'
app.config["SESSION_COOKIE_SECURE"] = True
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(hours=12)

# Proxy fix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=NB_REVERSE_PROXY, x_proto=NB_REVERSE_PROXY)

logger.info("Initialisation flask extensions")

# CSRF protection
csrf = CSRFProtect()
csrf.init_app(app)


# flask bcrypt
bcrypt = Bcrypt(app)

# sqlalchemy database
db = SQLAlchemy()
db.init_app(app)
migrate = Migrate(app, db,render_as_batch=True)


# login manager
from app.models import Users

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login.login"

@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))


# socketio
socketio = SocketIO(app)


# Session manager
session = Session(app)

# APSchelduler
from app.utils.tasks import read_CPU, read_RAM, read_NET, retention_files, maitenance_server
from app.models import Setup
logging.getLogger('apscheduler').setLevel(logging.ERROR)

scheduler = APScheduler()
scheduler.api_enabled = False
scheduler.init_app(app)
scheduler.add_job(trigger="interval", id="readCPU", func=read_CPU, seconds=60)
scheduler.add_job(trigger="interval", id="readRAM", func=read_RAM, seconds=60)
scheduler.add_job(trigger="interval", id="readNET", func=read_NET, seconds=60)
scheduler.add_job(trigger="cron", id="retentionFiles", func=retention_files, day="*", month="*", hour=1, minute=0)

# Maintenance server job
with app.app_context():
	query_maintenace = Setup.query.filter_by(action="ret").first()
# if query_retention != None:
	
# scheduler.add_job(trigger="cron", id="retentionFiles", func=maitenance_server, day="*")


scheduler.start()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


# Import all views
from app import views
