import sys

from flask import Flask

# socketio = SocketIO()


def create_app(config_filename):
    """Create an application."""
    dir = sys.path[0]
    app = Flask(__name__, template_folder=dir+'/templates', static_folder=dir+'/static')

    app.config.from_object(config_filename)
    # #setup user management
    # app.config.from_object(__name__+'.ConfigClass')
    # user_setup(app)
    from userver.database.db_sql import db_sql
    db_sql.init_app(app)

    with app.app_context():
        from userver.user import models
        from userver.object import application, gateway, device
        db_sql.create_all()

    from userver.main import register
    register(app)

    from flask_mail import Mail
    Mail(app)

    from userver.user import init_user
    init_user(app)

    # from gevent import monkey
    # monkey.patch_all()

    # socketio.init_app(app, async_mode='gevent')

    return app

