from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_cors import CORS  # 需要安装 flask-cors 库：pip install flask-cors

from flask_login import LoginManager

import os
from datetime import timedelta

from flask_session import Session

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "login"
login_manager.login_message_category = "info"


db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()


app = Flask(__name__)


def create_app():
    app = Flask(
        __name__, template_folder="../../templates", static_folder="../../static"
    )
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # 或 'None' 如果使用 HTTPS
    # app.config['SESSION_COOKIE_SECURE'] = False  # 确保仅通过 HTTPS 发送 Cookie

    CORS(app, supports_credentials=True)

    app.secret_key = "secret-key"

    # 配置 SQLite 数据库
    basedir = os.path.abspath(os.path.dirname(__file__))

    os.makedirs(os.path.join(basedir, "data"), exist_ok=True)

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "data", "optiflux_mlops.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    session_dir = os.path.join(basedir, "data", "flask_session")
    if not os.path.exists(session_dir):
        os.makedirs(session_dir)

    # 配置 Flask 会话
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = True  # 启用持久会话

    app.config["SESSION_FILE_DIR"] = session_dir
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_KEY_PREFIX"] = "session:"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)  # 设置 Session 有效期

    # 配置 Cookie
    app.config["SESSION_COOKIE_NAME"] = "session_cookie"
    app.config["SESSION_COOKIE_DOMAIN"] = None  # 或者设置为你的域名
    app.config["SESSION_COOKIE_PATH"] = "/"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # 如果使用 HTTPS，设置为 True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # 或者 'Strict' 或 'None'

    # app.config['SESSION_SERIALIZATION_FORMAT'] = 'json'

    Session(app)

    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)

    return app
