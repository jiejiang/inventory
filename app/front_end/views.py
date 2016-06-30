__author__ = 'jie'

from flask import send_file, render_template, current_app
from . import front_end

@front_end.route("/")
def index():
    api_prefix = "/api/v1.0"
    if 'ROUTE_PREFIX' in current_app.config:
        api_prefix = "/" + current_app.config['ROUTE_PREFIX'] + api_prefix
    return render_template('front_end.html', api_prefix=api_prefix, route_prefix=current_app.config['ROUTE_PREFIX'])
