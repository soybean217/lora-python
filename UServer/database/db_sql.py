from flask_sqlalchemy import SQLAlchemy
# db_sql = SQLAlchemy(session_options={'expire_on_commit':True})
db_sql = SQLAlchemy()
from flask import current_app
from urllib.parse import urlparse
