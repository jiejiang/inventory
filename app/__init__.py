__author__ = 'jie'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_bower import Bower
from flask_assets import Environment, Bundle
from flask_sqlalchemy import SQLAlchemy
from flask_rq import RQ
from flask_user import UserManager, UserMixin, SQLAlchemyAdapter

db = SQLAlchemy()
user_manager = None

class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
front-end server
    to add these headers, to let you quietly bind this to a URL other
than /
    and to an HTTP scheme that is different than what is used locally.

    In nginx:
        location /myprefix {
            proxy_pass http://192.168.0.1:5001;     # where Flask app runs
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Scheme $scheme;
            proxy_set_header X-Script-Name /myprefix;
            }

    :param app: the WSGI application
    '''

    def __init__(self, app, route_prefix=None):
        self.app = app
        self.route_prefix = route_prefix

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '/%s' % self.route_prefix if self.route_prefix else '')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]
            self.script_name = script_name

        scheme = environ.get('HTTP_X_SCHEME', '')
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        return self.app(environ, start_response)

def create_app():
    global user_manager

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)
    app.config.from_pyfile('local_config.py', silent=True)

    ROUTE_PREFIX = app.config['ROUTE_PREFIX'] if 'ROUTE_PREFIX' in app.config else None
    if ROUTE_PREFIX:
        app.wsgi_app = ReverseProxied(app.wsgi_app, ROUTE_PREFIX)

    Bootstrap(app)
    Bower(app)
    Environment(app)
    RQ(app)
    db.init_app(app)

    from models import User
    db_adapter = SQLAlchemyAdapter(db, User)
    user_manager = UserManager(db_adapter, app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api_1_0 import blueprint as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    from front_end import front_end
    app.register_blueprint(front_end, url_prefix='/app')

    from .admin import admin
    admin.init_app(app)

    return app

app = create_app()
