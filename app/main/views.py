__author__ = 'jie'

from flask import redirect, url_for
from . import main

@main.route("/", methods=['GET', 'POST'])
def index():
    return redirect(url_for('front_end.index'))

