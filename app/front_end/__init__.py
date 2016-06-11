__author__ = 'jie'

from flask import Blueprint

front_end = Blueprint('front_end', __name__, static_folder='static', template_folder='templates')

from . import views
