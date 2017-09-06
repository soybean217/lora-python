import json
from . import api, root
from flask import request
from ..http_auth import auth
from .forms.form_auth import LoginForm
from userver.user.admin import Admin


@api.route(root + 'login', methods=['POST'])
def login():
    if request.method == 'POST':
        login_form = LoginForm(request.form, csrf_enabled=False)
        if login_form.validate():
            admin = Admin.query.filter_by(username=login_form.username.data).first()
            if not admin:
                return json.dumps({'error': 'username %s does not exists' % login.username.data}), 401
            elif not admin.verify_password(login_form.password.data):
                return json.dumps({'error': 'username/password do not match'}), 401
            else:
                return '',201
        else:
            return json.dumps({'error': login_form.errors}), 401
