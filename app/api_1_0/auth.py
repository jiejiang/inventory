
from flask.ext import restful
from app import user_manager
from functools import wraps
from flask import current_app, request
from flask.ext.login import current_user

def _call_or_get(function_or_property):
    return function_or_property() if callable(function_or_property) else function_or_property

def http_basic_auth(authorization):
    if authorization is None or not 'username' in authorization or not 'password' in authorization:
        restful.abort(401, message='Unauthorized!')

    user = user_manager.find_user_by_username(authorization['username'])
    if user is None or not user_manager.verify_password(authorization['password'], user):
        restful.abort(401, message='Unauthorized!')

def login_required(func):
    """ This decorator ensures that the current user is logged in before calling the actual view.
        Calls the unauthorized_view_function() when the user is not logged in."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        # User must be authenticated
        if not _call_or_get(current_user.is_authenticated):
            # Redirect to unauthenticated page
            http_basic_auth(request.authorization)

        # Call the actual view
        return func(*args, **kwargs)
    return decorated_view