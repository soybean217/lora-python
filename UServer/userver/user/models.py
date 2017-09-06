from database.db_sql import db_sql as db
from sqlalchemy import PrimaryKeyConstraint
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                          BadSignature, SignatureExpired)
from flask import current_app
from . import passwords
import time
from sqlalchemy.orm import relationship


class User(db.Model):
    __bind_key__ = 'lorawan'
    __table_args__ = {'schema': 'lorawan'}
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)

    # User email information
    email = db.Column(db.String(255), nullable=False, unique=True)

    # User authentication information
    password = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=True)
    confirmed_at = db.Column(db.DateTime())
    confirm_email_token = db.Column(db.String(100), nullable=True)

    # User information
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)

    # Relationships
    roles = relationship('Role', secondary='lorawan.user_roles')

    apps = relationship('Application')
    gateways = relationship('Gateway')

    def generate_auth_token(self, expiration=600):
        s = Serializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None   # valid token, but expired
        except BadSignature:
            return None    # invalid token
        user = User.query.get(data['id'])
        return user

    def verify_password(self, password):
        """
        Make it backward compatible to legacy password hash.
        In addition, if such password were found, update the user's password field.
        """
        hashed_password = self.password
        verified = passwords.verify_password(current_app.user_manager, password, hashed_password)
        return verified

    def role_name_list(self):
        name_list = []
        for role in self.roles:
            name_list.append(role.name)
        return name_list


    def obj_to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'roles': self.role_name_list(),
            'confirmed_at': str(self.confirmed_at),
            'active': str(self.active),
            'app_num': self.apps.__len__(),
            'gateway_num': self.gateways.__len__()
        }



# Define the Role data model
class Role(db.Model):
    __bind_key__ = 'lorawan'
    __table_args__ = {'schema': 'lorawan'}
    __tablename__ = 'role'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


# Define the UserRoles data model
class UserRoles(db.Model):
    __bind_key__ = 'lorawan'
    __tablename__ = 'user_roles'
    __table_args__ = {'schema': 'lorawan'}

    db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('lorawan.user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('lorawan.role.id', ondelete='CASCADE'))
    PrimaryKeyConstraint(user_id, role_id)


class UserInvitation(db.Model):
    __bind_key__ = 'lorawan'
    __tablename__ = 'user_invite'
    __table_args__ = {'schema': 'lorawan'}

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255))
    # save the user of the invitee
    invited_by_user_id = db.Column(db.Integer, db.ForeignKey('lorawan.user.id'))
    # token used for registration page to identify user registering
    token = db.Column(db.String(100), nullable=False, server_default='')
    used_by = db.Column(db.Integer, db.ForeignKey('lorawan.user.id'))
    create_at = db.Column(db.DateTime(), nullable=False)
    expired = db.Column(db.Boolean())