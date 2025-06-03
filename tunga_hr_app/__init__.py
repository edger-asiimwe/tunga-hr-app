import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail

from config import config

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app(config_name):

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    CORS(app, supports_credentials=True, expose_headers='Authorization', allow_headers=['Content-Type', 'Authorization'])

    with app.app_context():

        # Import blueprints from all modules
        from .account import account as account_blueprint
        from .auth import auth as auth_blueprint

        # Register the blueprints with the application object
        app.register_blueprint(account_blueprint, url_prefix='/account')
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        if not app.debug and not app.testing:
            if app.config['LOG_TO_STDOUT']:
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = RotatingFileHandler('logs/microblog.log',
                                                maxBytes=10240, backupCount=10)
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s '
                    '[in %(pathname)s:%(lineno)d]'))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler) 

        app.logger.setLevel(logging.INFO)
        app.logger.info('Starting Cherio Backend')

        app.config.from_prefixed_env()

        return app

from .models import public, tenant