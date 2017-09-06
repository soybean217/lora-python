from database.db_sql import db_sql as db
from sqlalchemy import Column, String
from .models import User


class Client(db.Model):
    __bind_key__ = 'lorawan'
    __table_args__ = {'schema': 'lorawan'}
    name = Column(String(40))
    client_id = Column(String(40), primary_key=True)
    client_secret = Column(String(55), unique=True, index=True, nullable=False)

    # public or confidential
    is_confidential = Column(db.Boolean)

    _redirect_uris = Column(db.Text)
    _default_scopes = Column(db.Text)

    @property
    def client_type(self):
        if self.is_confidential:
            return 'confidential'
        return 'public'

    @property
    def redirect_uris(self):
        if self._redirect_uris:
            return self._redirect_uris.split()
        return []

    @property
    def default_redirect_uri(self):
        try:
            return self.redirect_uris[0]
        except IndexError:
            return ''

    @property
    def default_scopes(self):
        if self._default_scopes:
            return self._default_scopes.split()
        return []


class Token(db.Model):
    __bind_key__ = 'lorawan'
    __table_args__ = {'schema': 'lorawan'}
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(40), db.ForeignKey(Client.client_id), nullable=False,)
    client = db.relationship('Client')

    user_id = db.Column(db.Integer, db.ForeignKey(User.id))

    user = db.relationship('User')

    # currently only bearer is supported
    token_type = db.Column(db.String(40))

    access_token = db.Column(db.String(255), unique=True)
    refresh_token = db.Column(db.String(255), unique=True)
    expires = db.Column(db.DateTime)
    _scopes = db.Column(db.Text)

    def delete(self):
        db.session.delete(self)
        db.session.commit()
        return self

    @property
    def scopes(self):
        if self._scopes:
            return self._scopes.split()
        return []
#
# db.create_all()
