from flask_sqlalchemy import SQLAlchemy
# db_sql = SQLAlchemy(session_options={'expire_on_commit':True})
db_sql = SQLAlchemy()
from flask import current_app
from urllib.parse import urlparse


def create_fk(column, schema=None, **kwargs):
    if schema:
        column = "%s.%s" % (schema, column)
    return db_sql.ForeignKey(column, **kwargs)


def find_schema(cls):
    if hasattr(cls, '__bind_key__'):
        binds = current_app.config.get('SQLALCHEMY_BINDS')
        bind = binds.get(cls.__bind_key__)
    else:
        bind = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    return urlparse(bind).path.strip('/')
