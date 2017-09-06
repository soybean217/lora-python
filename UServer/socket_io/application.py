from userver.database.db_sql import db_sql, create_fk
from sqlalchemy import Column, String, BINARY, orm
import base64
from utils.errors import PasswordError
import pyDes
from binascii import hexlify


def cipher_token(key, token):
    """
    :param token: bytes
    :param app_eui: bytes
    :return:
    """
    myDes = pyDes.des(key, pyDes.ECB)
    token_cipher = myDes.encrypt(token)
    return base64.urlsafe_b64encode(token_cipher).decode().rstrip('=')


class Application(db_sql.Model):
    __tablename__ = 'app'
    app_eui = Column(BINARY(8), primary_key=True)
    name = Column(String(50))
    __token = Column(BINARY(16), name='token', nullable=False)
    user_id = db_sql.Column(db_sql.Integer())

    def auth_token(self, token):
        token_cipher = cipher_token(self.app_eui[0:8], self.__token)
        if token == token_cipher:
            return True
        else:
            raise PasswordError("APP:%s" % hexlify(self.app_eui).decode(), "TOKEN:%s" % token)