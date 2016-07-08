

__author__ = 'jie'

from flask import Blueprint, g, current_app
import flask_restful as restful
from flask_restful.representations.json import output_json
from flask_user import login_required

output_json.func_globals['settings'] = {'ensure_ascii': False, 'encoding': 'utf8'}

blueprint = Blueprint('api_1_0', __name__)

api = restful.Api(blueprint, decorators=[login_required,])

from . import views
