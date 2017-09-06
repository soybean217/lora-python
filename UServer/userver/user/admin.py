from database.db_sql import db_sql as db
from flask import current_app
from . import passwords
from sqlalchemy import Column, String, Integer


class Admin(db.Model):
    __bind_key__ = 'lorawan'
    __tablename__ = 'admin'

    __table_args__ = {'schema': 'lorawan'}

    id = Column(Integer, primary_key=True)

    # User email information
    username = Column(String(255), nullable=False, unique=True)

    # User authentication information
    password = Column(String(255), nullable=False)

    @staticmethod
    def hash_password(password):
        return passwords.hash_password(password)

    def verify_password(self, password):
        """
        Make it backward compatible to legacy password hash.
        In addition, if such password were found, update the user's password field.
        """
        hashed_password = self.password
        verified = passwords.verify_password(current_app.user_manager, password, hashed_password)
        return verified

