import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    APP_NAME = 'Tunga-HR'
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT') 

    BASE_CLIENT_URL = os.environ.get('BASE_CLIENT_URL')
    BASE_SERVER_URL = os.environ.get('BASE_SERVER_URL')

    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', True)
    MAIL_USE_SSL= os.environ.get('MAIL_USE_SSL', False)
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    ADMINS = ['support@cherio.tech']

    S3_BUCKET = os.environ.get('S3_BUCKET')
    S3_KEY = os.environ.get('S3_KEY')
    S3_SECRET = os.environ.get('S3_SECRET')
    S3_LOCATION = "https://{}.s3.amazonaws.com/".format(os.environ.get('S3_BUCKET'))

    ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND')

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.db')
    print('THIS APP IS IN DEBUG MODE. YOU SHOULD NOT SEE THIS IN PRODUCTION.')
    SQLALCHEMY_BINDS = {"public": SQLALCHEMY_DATABASE_URI}

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.db')
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_BINDS = {"public": SQLALCHEMY_DATABASE_URI}


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://')
    SSL_DISABLE = (os.environ.get('SSL_DISABLE') or 'True') == 'True'
    SQLALCHEMY_BINDS = {"public": SQLALCHEMY_DATABASE_URI}

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        assert os.environ.get('SECRET_KEY'), 'SECRET_KEY IS NOT SET!'


class HerokuConfig(ProductionConfig):
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        # Handle proxy server headers
        # from werkzeug.contrib.fixers import ProxyFix
        # app.wsgi_app = ProxyFix(app.wsgi_app)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
    'heroku': HerokuConfig,
}