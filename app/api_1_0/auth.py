
from flask.ext import restful
from app import user_manager

def http_basic_auth(authorization):
    if authorization is None or not 'username' in authorization or not 'password' in authorization:
        restful.abort(401, message='Unauthorized!')

    user = user_manager.find_user_by_username(authorization['username'])
    if user is None or not user_manager.verify_password(authorization['password'], user):
        restful.abort(401, message='Unauthorized!')
