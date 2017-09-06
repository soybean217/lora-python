from flask import Blueprint, current_app, Flask
from flask_login import current_user
from .user_manager import UserManager

from .models import Role, User
from .admin import Admin
from database.db_sql import db_sql
from datetime import datetime


def _flask_user_context_processor():
    """ Make 'flask_user' available to Jinja2 templates"""
    return dict(
        user_manager=current_app.user_manager,
        user=current_user)


def init_user(app):

    app.user_manager = UserManager(app)

    # Add context processor
    app.context_processor(_flask_user_context_processor)

    with app.app_context():
        create_admin_user(app)


def create_admin_user(app):
    if not Admin.query.filter(Admin.username == 'gis').first():
        admin = Admin(username='gis', password=Admin.hash_password('gg123456'))
        db_sql.session.add(admin)
        db_sql.session.commit()
    if not Role.query.filter(Role.name == 'admin').first():
        role1 = Role(name="admin")
        db_sql.session.add(role1)
        db_sql.session.commit()

    if not User.query.filter(User.email == 'zhangjiayi@niot.cn').first():
        user1 = User(email='zhangjiayi@niot.cn', active=True,
                     password=app.user_manager.hash_password('lw123456'))
        user1.confirmed_at = datetime.utcnow()
        user1.roles.append(Role.query.filter(Role.name == 'admin').first())
        db_sql.session.add(user1)
        db_sql.session.commit()

    if not User.query.filter(User.email == 'kevinwood717@gmail.com').first():
        user1 = User(email='kevinwood717@gmail.com', active=True,
                     password=app.user_manager.hash_password('123456a'))
        user1.confirmed_at = datetime.utcnow()
        user1.roles.append(Role.query.filter(Role.name == 'admin').first())
        db_sql.session.add(user1)
        db_sql.session.commit()

