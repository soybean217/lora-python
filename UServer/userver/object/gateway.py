from database.db0 import db0, ConstDB
from database.db3 import db3, ConstDB3
from utils.errors import KeyDuplicateError, ReadOnlyDeny
from utils.utils import eui_64_to_48, eui_48_to_64
from binascii import hexlify
from enum import Enum
import enum

from userver.frequency_plan import FrequencyPlan
from userver.object.asserts import Assertions
from userver.user.models import User

from sqlalchemy import Column, String, BINARY
from sqlalchemy import orm, ForeignKey
from database.db_sql import db_sql
import eviltransform


class Platform(Enum):
    rpi = 'Raspberry Pi'
    rpi3 = 'Raspberry Pi 3'
    linklabs = 'LinkLabs'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Platform), '%r is not a valid Platform' % value


class Model(Enum):
    imst = 'IMST'
    linklabs = 'LinkLabs'
    menthink = 'MenThink'
    risinghf = 'RisingHF'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Model), '%r is not a valid Model' % value


class Field:
    id = 'id'
    mac_addr = 'mac_addr'
    name = 'name'
    platform = 'platform'
    model = 'model'
    freq_plan = 'freq_plan'
    public = 'public'
    disable = 'disable'
    time = 'time'
    lng = 'lng'
    lat = 'lat'
    alt = 'alt'
    location = 'location'
    user_id = 'user_id'
    restart = 'restart'


class Location:
    _assert_switcher = {Field.lng: Assertions.a_float,
                        Field.lat: Assertions.a_float,
                        Field.alt: Assertions.a_int, }

    def __setattr__(self, key, value):
        self._assert_switcher[key](value)
        self.__dict__[key] = value

    def __init__(self, lng, lat, alt):
        self.lng = lng
        self.lat = lat
        self.alt = alt
        self.switch_wgs2gcj()

    def __str__(self):
        return '%s,%s,%s' % (self.lng, self.lat, self.alt)

    def obj_to_dict(self):
        info = {}
        for key, value in self.__dict__.items():
            if key in (Field.lng, Field.lat, Field.alt):
                info[key] = value
        return info

    def switch_wgs2gcj(self):
        self.lat, self.lng = eviltransform.wgs2gcj(self.lat, self.lng)

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Location), '%r is not a valid Location' % value

    class objects:
        @staticmethod
        def str_to_obj(string):
            string = string.split(',')
            try:
                return Location(float(string[0]), float(string[1]), int(string[2]))
            except Exception as error:
                raise error


class Gateway(db_sql.Model):
    redis_fields = (Field.user_id, Field.platform, Field.model, Field.freq_plan, Field.public, Field.disable, Field.location)
    __vars_can_write = (Field.platform, Field.model, Field.freq_plan, Field.public, Field.disable, Field.name, Field.location)
    _assert_switcher = {
                        Field.user_id: Assertions.a_not_negative_int,
                        Field.id: Assertions.a_eui_64,
                        Field.mac_addr: Assertions.a_eui_48,
                        Field.name: Assertions.a_str,
                        Field.platform: Platform.assert_isinstanceof,
                        Field.freq_plan: FrequencyPlan.assert_isinstanceof,
                        Field.model: Model.assert_isinstanceof,
                        Field.public: Assertions.a_bool,
                        Field.disable: Assertions.a_bool,
                        Field.restart: Assertions.a_bool,
                        Field.location: Location.assert_isinstanceof,
                        Field.time: Assertions.a_int,
                        }

    __table_args__ = {'schema': 'nwkserver'}
    __tablename__ = 'gateway'

    id = Column(BINARY(8), primary_key=True)
    name = Column(String(50))
    user_id = db_sql.Column(db_sql.Integer(), ForeignKey(User.id, ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    @orm.reconstructor
    def init_on_load(self):
        self.mac_addr = eui_64_to_48(self.id)
        info = db0.hgetall(ConstDB.gateway + hexlify(self.id).decode())
        self.freq_plan = FrequencyPlan(info[b'freq_plan'].decode())
        self.public = bool(int(info[b'public']))
        self.disable = bool(int(info[b'disable']))
        self.platform = Platform[info[b'platform'].decode()]
        self.model = Model[info[b'model'].decode()]
        location = info.get(b'location')
        if location is not None:
            self.location = Location.objects.str_to_obj(location.decode())
        else:
            self.location = Location(0.0, 0.0, 0)
        time = db3.get(ConstDB3.T_GATEWAY + hexlify(self.id).decode())
        if time is not None:
            self.time = int(time)

    def __setattr__(self, key, value):
        try:
            attr = getattr(self, key)
            if attr is not None and key not in self.__vars_can_write:
                raise ReadOnlyDeny
        except AttributeError:
            pass
        if key in self._assert_switcher:
            self._assert_switcher[key](value)
        super.__setattr__(self, key, value)

    def __init__(self, user_id, mac_addr, name, platform, model, freq_plan=FrequencyPlan.EU863_870, public=True, disable=False, location=None):
        """
        :param id: 8 bytes
        :param name: str
        :param platform: Platform
        :return:
        """
        self.user_id = user_id
        self.id = eui_48_to_64(mac_addr)
        self.name = name
        self.platform = platform
        self.freq_plan = freq_plan
        self.public = public
        self.disable = disable
        self.model = model
        if location is not None:
            self.location = location
        else:
            self.location = Location(0.0, 0.0, 0)

    def _zip_vars(self):
        return dict(zip(self.redis_fields,
                        (self.user_id, self.platform.name, self.model.name, self.freq_plan.value, self.public.real, self.disable.real, str(self.location))))

    def _zip_vars_can_write(self):
        dd = {}
        for field in self.redis_fields:
            if field in self.__vars_can_write:
                value = getattr(self, field)
                if isinstance(value, enum.Enum):
                    value = value.value if field == Field.freq_plan else value.name
                elif isinstance(value, bool):
                    value = value.real
                dd[field] = value
        return dd

    def send_restart_request(self):
        db0.hset(ConstDB.gateway + hexlify(self.id).decode(), 'restart', 1)

    def save(self):
        db_sql.session.add(self)
        id_str = hexlify(self.id).decode()
        key = ConstDB.gateway + id_str
        if db0.exists(key):
            raise KeyDuplicateError(key)
        db0.hmset(key, self._zip_vars())
        #save to sql
        db_sql.session.commit()
        db_sql.session.registry.clear()

    def update(self):
        print(self._zip_vars_can_write())
        db0.hmset(ConstDB.gateway + hexlify(self.id).decode(), self._zip_vars_can_write())
        db_sql.session.commit()

    def delete(self):
        db_sql.session.delete(self)
        db_sql.session.commit()
        # delete from sql
        id = hexlify(self.id).decode()
        gateway_trans = db0.keys(pattern=ConstDB.trans_params + '*' + id)
        pipe = db0.pipeline()
        for key in gateway_trans:
            key = key.decode()
            pipe.delete(key)
            dev_eui = key.split(":")[1]
            pipe.zrem(ConstDB.dev_gateways + dev_eui, self.id)
        pipe.delete(ConstDB.gateway + id)
        pipe.delete(ConstDB.gateway_pull + id)
        pipe.execute()

    def obj_to_dict(self):
        dd = {
              'id': hexlify(self.id).decode().upper(),
              'mac_addr': hexlify(self.mac_addr).decode().upper(),
              'name': self.name,
              'platform': self.platform.value,
              'model': self.model.value,
              'freq_plan': self.freq_plan.value,
              'public': self.public,
              'disable': self.disable,
              'location': self.location.obj_to_dict(),
        }
        if hasattr(self, 'time'):
            dd['last_data'] = self.time
        self.get_pull_info()
        if hasattr(self, 'ip_addr'):
            dd['ip'] = self.ip_addr
        if hasattr(self, 'prot_ver'):
            dd['ver'] = self.prot_ver
        return dd

    def get_pull_info(self):
        key = ConstDB.gateway_pull + hexlify(self.id).decode()
        info = db0.hgetall(key)
        if info:
            self.ip_addr = info[b'ip_addr'].decode()
            self.prot_ver = int(info[b'prot_ver'])


if __name__ == '__main__':
    print(Model('IMST'))