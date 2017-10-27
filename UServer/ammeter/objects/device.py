from binascii import hexlify
import json
import enum
from database.db1 import db1, Tables1, Channel1
from database.db0 import db0, ConstDB
from utils.log import logger
from utils.errors import KeyDuplicateError, ReadOnlyDeny
from userver.object.const import FieldDevice
from userver.object.asserts import Assertions
from datetime import datetime, timezone
OTAA_EXPIRE = 5

from sqlalchemy import Float, Column, BINARY, PrimaryKeyConstraint, Integer, ForeignKey, Numeric, Enum, DATETIME
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI


Base = declarative_base()


class ActiveMode(enum.Enum):
    abp = 'abp'
    otaa = 'otaa'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, ActiveMode), '%r is not a valid ActiveMode' % value


class ClassType(Enum):
    a = 'A'
    b = 'B'
    c = 'C'


class Device(Base):
    __tablename__ = 'device'

    __redis_fields = (FieldDevice.app_eui,
                      FieldDevice.addr,
                      FieldDevice.nwkskey,
                      FieldDevice.appskey,
                      FieldDevice.fcnt_up,
                      FieldDevice.fcnt_down,
                      FieldDevice.dev_class,
                      FieldDevice.adr,
                      FieldDevice.check_fcnt,)

    __assert_switcher = {FieldDevice.active_at: Assertions.a_datetime,
                        FieldDevice.active_mode: ActiveMode.assert_isinstanceof,
                        FieldDevice.dev_eui: Assertions.a_eui_64,
                        FieldDevice.addr: Assertions.a_dev_addr,
                        FieldDevice.app_eui: Assertions.a_eui_64,
                        FieldDevice.nwkskey: Assertions.a_nwkskey,
                        FieldDevice.appskey: Assertions.a_appskey,
                        FieldDevice.fcnt_up: Assertions.a_fcnt,
                        FieldDevice.fcnt_down: Assertions.a_fcnt,
                        FieldDevice.dev_class: Assertions.a_dev_class,
                        FieldDevice.adr: Assertions.a_bool,
                        FieldDevice.check_fcnt: Assertions.a_bool, }

    dev_eui = Column(BINARY(8), primary_key=True)
    app_eui = Column(BINARY(8), nullable=False)
    active_mode = Column(Enum(ActiveMode), nullable=True)
    active_at = Column(DATETIME)

    def active(self, addr, nwkskey, appskey=None, fcnt_up=0, fcnt_down=0, dev_class=ClassType.a, adr=True, check_fcnt=False):
        self.addr = addr
        self.nwkskey = nwkskey
        if appskey is None:
            appskey = b''
        self.appskey = appskey
        self.addr = addr
        self.addr = addr
        self.fcnt_up = fcnt_up
        self.fcnt_down = fcnt_down
        self.dev_class = dev_class
        self.adr = adr
        self.check_fcnt = check_fcnt
        key_eui = ConstDB.dev + hexlify(self.dev_eui).decode()
        pipe = db0.pipeline()
        pipe.hmset(key_eui, self.__zip_vars())
        pipe.set(ConstDB.addr + hexlify(self.addr).decode(), key_eui)
        pipe.execute()

    def __zip_vars(self):
        dd = {}
        for field in self.__redis_fields:
            value = getattr(self, field)
            if isinstance(value, enum.Enum):
                value = value.value
            elif isinstance(value, bool):
                value = value.real
            dd[field] = value
        return dd

    def publish(self):
        message = {'dev_eui': hexlify(self.dev_eui).decode(),
                   'addr': hexlify(self.addr).decode(),
                   'nwkskey': hexlify(self.nwkskey).decode(),
                   'appskey': hexlify(self.appskey).decode(),
                   'ts':self.active_at.replace(tzinfo=timezone.utc).timestamp(),
                   }
        db0.publish(Channel1.join_success_alarm + hexlify(self.app_eui).decode(), json.dumps(message))

class JoiningDev:
    fields = (FieldDevice.app_eui, FieldDevice.addr)

    __vars_can_write = (FieldDevice.nwkskey, FieldDevice.appskey)

    _assert_switcher = {FieldDevice.dev_eui: Assertions.a_eui_64,
                        FieldDevice.app_eui: Assertions.a_eui_64,
                        FieldDevice.addr: Assertions.a_dev_addr,
                        FieldDevice.nwkskey: Assertions.a_nwkskey,
                        FieldDevice.appskey: Assertions.a_appskey
                        }

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise ReadOnlyDeny
        self._assert_switcher[key](value)
        assert_method = self._assert_switcher.get(key)
        if assert_method is not None:
            self._assert_switcher[key](value)
        super.__setattr__(self, key, value)

    def __init__(self, app_eui, dev_eui, addr, nwkskey=None, appskey=None):
        self.app_eui = app_eui
        self.dev_eui = dev_eui
        self.addr = addr
        if nwkskey is not None:
            self.nwkskey = nwkskey
        if appskey is not None:
            self.appskey = appskey

    def __zip_vars(self):
        return dict(zip(self.fields, (self.app_eui, self.addr)))

    def __zip_vars_can_write(self):
        return dict(zip(self.__vars_can_write, (self.nwkskey, self.appskey)))

    def save(self):
        key_eui = Tables1.dev + hexlify(self.dev_eui).decode()
        key_addr = Tables1.addr + hexlify(self.addr).decode()
        # if db1.exists(key_eui) or db0.exists(key_eui):
        if db1.exists(key_eui):
            raise KeyDuplicateError(key_eui)
        if db1.exists(key_addr) or db0.exists(key_addr):
            raise KeyDuplicateError(key_addr)
        pipe = db1.pipeline()
        pipe.hmset(key_eui, self.__zip_vars())
        pipe.set(key_addr, key_eui)
        pipe.expire(key_addr, OTAA_EXPIRE-2)
        pipe.expire(key_eui, OTAA_EXPIRE-2)
        pipe.execute()

    def update(self):
        db1.hmset(Tables1.dev + hexlify(self.dev_eui).decode(), self.__zip_vars_can_write())

    def delete(self):
        key_eui = Tables1.dev + hexlify(self.dev_eui).decode()
        key_addr = Tables1.addr + hexlify(self.addr).decode()
        pipe = db1.pipeline()
        pipe.delete(key_eui)
        pipe.delete(key_addr)
        pipe.execute()

    class objects:
        @staticmethod
        def get(dev_eui):
            info = db1.hgetall(Tables1.dev + hexlify(dev_eui).decode())
            try:
                join_dev = JoiningDev(dev_eui=dev_eui, app_eui=info[b'app_eui'], addr=info[b'addr'], nwkskey=info.get(b'nwkskey'), appskey=info.get(b'appskey'))
                return join_dev
            except (KeyError, AssertionError) as error:
                logger.error('Join Success' + str(error))


# Create an engine that stores data in the local directory's
# sqlalchemy_example.db file.
engine = create_engine(SQLALCHEMY_DATABASE_URI)

DBSession = sessionmaker(bind=engine)

db_session = DBSession()