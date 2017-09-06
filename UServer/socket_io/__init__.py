from utils.utils import display_hex, display_hex_hyphen, ts_to_iso


# def register(app):
#     app.jinja_env.globals['hex'] = display_hex
#     app.jinja_env.globals['hex_hyphen'] = display_hex_hyphen
#     app.jinja_env.globals['ts_to_iso'] = ts_to_iso

from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()


def create_app(config_filename):
    """Create an application."""
    app = Flask(__name__)

    app.config.from_object(config_filename)

    from userver.database.db_sql import db_sql
    db_sql.init_app(app)
    # with app.test_request_context():
    #    from userver.object import application

    # register(app)

    from gevent import monkey
    monkey.patch_all()

    socketio.init_app(app, async_mode='gevent')

    from . import events

    from .events import WatchThreadThreading
    thr = WatchThreadThreading()
    thr.start()

    return app