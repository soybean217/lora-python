from flask import Flask
from flask.ext.cors import CORS


def create_api_server(config_filename):
    app = Flask(__name__)

    app.config.from_object(config_filename)

    from userver.database.db_sql import db_sql
    db_sql.init_app(app)

    with app.test_request_context():
        from userver.user import models
        from userver.object import device
        from userver.object import application
        from userver.object import gateway
        db_sql.create_all()

    from userver.user import init_user
    init_user(app)

    from flask_mail import Mail
    Mail(app)

    from .api import register
    register(app)

    CORS(app, resource={r"/*": {"origins": "http://"+app.config['HOST']+':8888'}})

    return app