import base64
import uuid
from binascii import unhexlify, hexlify
import pyDes
from sqlalchemy.exc import IntegrityError

from userver.object.asserts import Assertions
from userver.frequency_plan import FrequencyPlan
from database.db0 import db0, ConstDB
from utils.errors import ReadOnlyDeny, PasswordError, ResourceAlreadyExistError
from utils.utils import base64_decode_urlsafe

# from userver.user.models import Application as App
from sqlalchemy import Column, String, BINARY, Integer, ForeignKey
from sqlalchemy import orm, select, func
from sqlalchemy.orm import relationship, object_session
from database.db_sql import db_sql
from userver.user.models import User
from database.db2 import ConstDB2, db2

def generate_random_token():
    """
    :return: 16 bytes
    """
    token = uuid.uuid4().bytes
    return token


def cipher_token(key, token):
    """
    :param token: bytes
    :param app_eui: bytes
    :return:
    """
    myDes = pyDes.des(key, pyDes.ECB)
    token_cipher = myDes.encrypt(token)
    return base64.urlsafe_b64encode(token_cipher).decode().rstrip('=')


def decrypt_token(token_cipher, app_eui):
    """
    :param token_cipher:
    :param app_eui:bytes
    :return:
    """
    myDes = pyDes.des(app_eui, pyDes.ECB)
    token_cipher = base64_decode_urlsafe(token_cipher)
    token = myDes.decrypt(token_cipher)
    return token


class Field:
    user_id = 'user_id'
    app_eui = 'app_eui'
    name = 'name'
    token = '_Application__token'
    token_cipher = 'token_cipher'
    freq_plan = 'freq_plan'
    appkey = 'appkey'


class Application(db_sql.Model):
    redis_fields = (Field.user_id, Field.freq_plan, )
    _vars_can_write = (Field.name, Field.freq_plan, Field.token, Field.token_cipher, Field.appkey)
    _assert_switcher = {
                        Field.user_id: Assertions.a_not_negative_int,
                        Field.app_eui: Assertions.a_eui_64,
                        Field.name: Assertions.a_str,
                        Field.token: Assertions.a_token,
                        Field.freq_plan: FrequencyPlan.assert_isinstanceof,
                        }
    __tablename__ = 'app'
    __table_args__ = {'schema': 'nwkserver'}

    app_eui = Column(BINARY(8), primary_key=True)
    name = Column(String(50))
    __token = Column(BINARY(16), name='token', nullable=False)
    user_id = Column(Integer(), ForeignKey(User.id, ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    appkey = Column(BINARY(16))
    http_push = relationship('HttpPush', uselist=False, cascade="delete")
    location_service = relationship('LocationService', uselist=False, cascade="delete")
    devices = relationship('Device', back_populates="app")

    def __init__(self, user_id, app_eui, name, freq_plan=FrequencyPlan.EU863_870, appkey=None):
        self.user_id = user_id
        self.app_eui = app_eui
        self.name = name
        self.freq_plan = freq_plan
        self.appkey = appkey
        self.__token = generate_random_token()

    @orm.reconstructor
    def init_on_load(self):
        if self.__token is not None:
            self.token_cipher = cipher_token(self.app_eui[0:8], self.__token)
        freq_plan = db0.hget(ConstDB.app + hexlify(self.app_eui).decode(), Field.freq_plan)
        if freq_plan is not None:
            self.freq_plan = FrequencyPlan(freq_plan.decode())
        else:
            self.freq_plan = FrequencyPlan.EU863_870

    def __setattr__(self, key, value):
        try:
            attr = getattr(self, key)
            if attr is not None and key not in self._vars_can_write:
                raise ReadOnlyDeny
        except AttributeError:
            pass
        if key in self._assert_switcher:
            self._assert_switcher[key](value)
        super.__setattr__(self, key, value)

    def __zip_vars(self):
        return dict(zip(self.redis_fields,
                        (self.user_id, self.freq_plan.value, )))

    def __zip_vars_can_write(self):
        return {Field.freq_plan: self.freq_plan.value, }

    def save(self):
        try:
            db_sql.session.add(self)
            db_sql.session.flush()
        except IntegrityError as e:
            raise ResourceAlreadyExistError('Application', self.app_eui)
        # save into redis
        key = ConstDB.app + hexlify(self.app_eui).decode()
        if db0.exists(key):
            raise ResourceAlreadyExistError('Application', self.app_eui)
        db0.hmset(key, self.__zip_vars())
        db_sql.session.commit()
        db_sql.session.registry.clear()

    def update(self):
        db0.hmset(ConstDB.app + hexlify(self.app_eui).decode(), self.__zip_vars_can_write())
        db_sql.session.commit()

    def delete(self):
        db_sql.session.delete(self)
        db_sql.session.flush()
        db0.delete(ConstDB.app + hexlify(self.app_eui).decode())
        db_sql.session.commit()

    def auth_token(self, token):
        if token == self.token_cipher:
            return True
        else:
            raise PasswordError("APP:%s" % hexlify(self.app_eui).decode(), "TOKEN:%s" % token)

    def generate_new_token(self):
        self.__token = generate_random_token()
        self.token_cipher = cipher_token(self.app_eui[0:8], self.__token)

    @staticmethod
    def __generate_random_token():
        """
        :return: 16 bytes
        """
        token = uuid.uuid4().bytes
        return token

    def obj_to_dict(self):
        return {'app_eui': hexlify(self.app_eui).decode().upper(),
                'token': self.token_cipher,
                'name': self.name,
                'freq_plan': self.freq_plan.value,
                'appkey': hexlify(self.appkey).decode().upper() if self.appkey else self.appkey,
                'device_num': self.devices.__len__(),
                'user': self.user_id}
                # 'group_num': self.groups.__len__(),}

    # def set_packet_expire(self, time):
    #     for device in self.devices:





# class JoinApplication(db_sql.Model):
#     __tablename__ = 'join_app'
#     app_eui = Column(BINARY(8), ForeignKey(Application.app_eui, ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)


class HttpPush(db_sql.Model):
    __tablename__ = 'http_push'

    __table_args__ = {'schema': 'nwkserver'}

    app_eui = db_sql.Column(BINARY(8), ForeignKey(Application.app_eui, ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    url = db_sql.Column(String(200), nullable=False)

    def obj_to_dict(self):
        return {'open': True, 'url': self.url}

    def add(self):
        db_sql.session.add(self)
        db_sql.session.commit()

    def delete(self):
        db_sql.session.delete(self)
        db_sql.session.commit()

    def update(self):
        db_sql.session.commit()


class LocationService(db_sql.Model):
    __tablename__ = 'location_service'

    __table_args__ = {'schema': 'nwkserver'}

    app_eui = db_sql.Column(BINARY(8), ForeignKey(Application.app_eui, ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)

    def delete(self):
        db_sql.session.delete(self)
        db_sql.session.commit()

    def add(self):
        db_sql.session.add(self)
        db_sql.session.commit()


# class ServiceName(enum.Enum):
#     http_push = 'http push'
#     location = 'location'
#
#
# class Service(db_sql.Model):
#     __tablename__ = 'service'
#
#     @declared_attr
#     def __table_args__(cls):
#         return {'schema': find_schema(cls)}
#
#     id = db_sql.Column(db_sql.Integer(), primary_key=True)
#     name = db_sql.Column(Enum(ServiceName), unique=True)
#
#     def obj_to_dict(self):
#         return {'name': self.name}
#
#
# class AppServices(db_sql.Model):
#     __tablename__ = 'app_services'
#
#     @declared_attr
#     def __table_args__(cls):
#         return {'schema': find_schema(cls)}
#
#     app_eui = db_sql.Column(BINARY(8), db_sql.ForeignKey('nwkserver.app.app_eui', ondelete='CASCADE'))
#     service_id = db_sql.Column(db_sql.Integer(), db_sql.ForeignKey('nwkserver.service.id', ondelete='CASCADE'))
#     PrimaryKeyConstraint(app_eui, service_id)
#     info = db_sql.Column(db_sql.String(200), nullable=True)
#     service = db_sql.relationship('Service')
#
#     def obj_to_dict(self):
#         return {'name': self.service.name,
#                 'info': self.info}
#
#     def delete(self):
#         db_sql.session.delete(self)
#         db_sql.session.commit()
#
#     def get(self, app_eui, service_name):
#         q = db_sql.session.query(AppServices).filter(AppServices.app_eui == app_eui).join(AppServices.service).filter(Service.name==service_name).first()
#         return q