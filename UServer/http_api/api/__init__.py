from flask import Blueprint, Flask

api = Blueprint('api', __name__)

# root = '/api/v1/'
root = '/'



def register(app):
    app.register_blueprint(api)


from . import api_group, api_app, api_device, api_gateway, api_msg, api_trans_status
