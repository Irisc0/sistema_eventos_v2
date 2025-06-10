from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
from datetime import datetime

from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = 'auth.index'

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes.auth import auth
    from app.routes.eventos import eventos
    app.register_blueprint(auth)
    app.register_blueprint(eventos)

    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}

    return app
