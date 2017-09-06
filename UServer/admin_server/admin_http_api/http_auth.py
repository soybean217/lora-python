from functools import wraps
from flask import make_response, request
from userver.user.admin import Admin
import time

"""
support basic auth
1、email and password
2、auth token(username=auth token, password='')
"""


class HTTPAuth:
    def __init__(self):
        # def default_get_password(username):
        #     return None
        def default_auth_error():
            return "Unauthorized Access"

        self.realm = "Authentication Required"
        # self.get_password(default_get_password)
        self.error_handler(default_auth_error)

    def error_handler(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            res = f(*args, **kwargs)
            if type(res) == str:
                res = make_response(res)
                res.status_code = 401
            if 'WWW-Authenticate' not in res.headers.keys():
                res.headers['WWW-Authenticate'] = 'Basic realm="' + self.realm + '"'
            return res
        self.auth_error_callback = decorated
        return decorated

    @staticmethod
    def verify_password(username, password):
        # first try to authenticate by token
        # user = Admin.verify_password(email_or_token, password)
        # if not user:
        #     # try to authenticate with username/password
        #     user = Admin.query.filter_by(email=email_or_token).first()
        #     if not user or not user.verify_password(password):
        #         return False
        admin = Admin.query.filter_by(username=username).first()
        if not admin:
            return False
        elif not admin.verify_password(password):
            return False
        return admin

    def auth_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth = request.authorization
            if not auth:
                return self.auth_error_callback()
            admin = self.verify_password(auth.username, auth.password)
            if not admin:
                return self.auth_error_callback()
            return f(*args, **kwargs)

        return decorated


auth = HTTPAuth()