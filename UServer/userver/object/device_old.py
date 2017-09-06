from binascii import hexlify, unhexlify
from userver.object.asserts import Assertions
from .const import FieldDevice, ClassType
from database.db0 import db0, ConstDB
from utils.errors import ReadOnlyDeny
from .que_down import QueDownDev
from .addr import AddrManger
from userver.frequency_plan import frequency_plan
from utils.log import Logger, Action, Resource


import enum
from database.db_sql import db_sql
from sqlalchemy import Column, String, BINARY, ForeignKey, DATETIME
from sqlalchemy.types import Enum
from sqlalchemy import orm
from sqlalchemy.orm import relationship
from .application import Application
from .trans_status import TransStatus

from time import time



class FieldInfo:
    MaxDutyCycle = 'MaxDutyCycle'
    RX1DRoffset = 'RX1DRoffset'
    RX2DataRate = 'RX2DataRate'
    RX2Frequency = 'RX2Frequency'
    RxDelay = 'RxDelay'
    battery = 'battery'
    snr = 'snr'


class ActiveMode(enum.Enum):
    abp = 'abp'
    otaa = 'otaa'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, ActiveMode), '%r is not a valid ActiveMode' % value


class Device(db_sql.Model):
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

    __vars_can_write = (FieldDevice.addr,
                       FieldDevice.nwkskey,
                       FieldDevice.appskey,
                       FieldDevice.name,
                       FieldDevice.fcnt_up,
                       FieldDevice.fcnt_down,
                       FieldDevice.dev_class,
                       FieldDevice.adr,
                       FieldDevice.check_fcnt,
                       FieldDevice.active_at,
                       'join_device',)

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

    _info_field = (FieldInfo.MaxDutyCycle, FieldInfo.RX1DRoffset, FieldInfo.RX2DataRate, FieldInfo.RX2Frequency, FieldInfo.RxDelay, FieldInfo.battery, FieldInfo.snr)

    dev_eui = Column(BINARY(8), primary_key=True)
    app_eui = Column(BINARY(8), ForeignKey(Application.app_eui, ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    name = Column(String(50))
    active_mode = Column(Enum(ActiveMode), nullable=True)
    active_at = Column(DATETIME)

    join_device = relationship('JoinDevice', uselist=False, lazy='joined', cascade='save-update, delete, delete-orphan')

    app = relationship('Application', cascade='save-update')

    def active(self, nwkskey, appskey=None, addr=None, fcnt_up=0, fcnt_down=0, dev_class=ClassType.a, adr=True, check_fcnt=False):
        self.nwkskey = nwkskey
        if appskey is None:
            appskey = b''
        self.appskey = appskey
        if self.active_mode == ActiveMode.abp:
            if addr is None:
                addr = AddrManger.dis_dev_addr()
        self.addr = addr
        AddrManger.addr_available(self.addr)
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

    @orm.reconstructor
    def init_on_load(self):
        if self.active_at:
            info = db0.hgetall(ConstDB.dev + hexlify(self.dev_eui).decode())
            try:
                self.addr = info[b'addr']
                self.nwkskey = info[b'nwkskey']
                self.appskey = info.get(b'appskey', b'')
                self.fcnt_up = int(info[b'fcnt_up'])
                self.fcnt_down = int(info[b'fcnt_down'])
                self.dev_class = ClassType(info[b'dev_class'].decode())
                self.adr = bool(int(info[b'adr']))
                self.check_fcnt = bool(int(info[b'check_fcnt']))
                self.que_down = QueDownDev(self.dev_eui)
                self.trans_status = TransStatus.objects.best(self.dev_eui)
                self.__get_more_info()
                if self.dev_class == ClassType.b:
                    self.get_b_info()
            except (KeyError, TypeError) as error:
                Logger.error(action=Action.get, resource=Resource.device, id=self.dev_eui, msg=str(error))

    def __eq__(self, other):
        return self.dev_eui == other.dev_eui

    def __repr__(self):
        return "Device %s" % (hexlify(self.dev_eui).decode())

    def __hash__(self):
        return hash(self.__repr__())

    def __setattr__(self, key, value):
        try:
            attr = getattr(self, key)
            if attr is not None and key not in self.__vars_can_write:
                raise ReadOnlyDeny
        except AttributeError:
            pass
        assert_method = self.__assert_switcher.get(key)
        if assert_method is not None:
            self.__assert_switcher[key](value)
        super.__setattr__(self, key, value)

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

    def __zip_vars_can_write(self):
        dd = {}
        for field in self.__redis_fields:
            if field in self.__vars_can_write:
                value = getattr(self, field)
                if isinstance(value, enum.Enum):
                    value = value.value
                elif isinstance(value, bool):
                    value = value.real
                dd[field] = value
        return dd

    def get_b_info(self):
        info = db0.hgetall(ConstDB.b + hexlify(self.dev_eui).decode())
        self.periodicity = info['periodicity'] if info else 0
        self.datr = info['datr'] if info else 0

    def update(self, fields):
        dd = {}
        pipe = db0.pipeline()
        dev_key = ConstDB.dev + hexlify(self.dev_eui).decode()
        for field in fields:
            if field.name in self.__redis_fields:
                if not self.active_at:
                    raise Exception('Device is not active yet')
                value = getattr(self, field.name)
                if field.name == FieldDevice.addr:
                    orignal_addr = db0.hget(dev_key, FieldDevice.addr)
                    if value != orignal_addr:
                        AddrManger.addr_available(self.addr)
                        pipe.rename(ConstDB.addr + hexlify(orignal_addr).decode(), ConstDB.addr + hexlify(self.addr).decode())
                if isinstance(value, enum.Enum):
                    value = value.value
                elif isinstance(value, bool):
                    value = value.real
                dd[field.name] = value
        if len(dd) > 0:
            pipe.hmset(dev_key, dd)
            pipe.execute()

    def delete(self):
        db_sql.session.delete(self)
        db_sql.session.flush()
        if self.active_at is not None:
            app_eui = hexlify(self.app_eui).decode()
            dev_eui = hexlify(self.dev_eui).decode()
            addr = hexlify(db0.hget(ConstDB.dev + dev_eui, FieldDevice.addr)).decode()
            msgs_up = db0.keys(ConstDB.msg_up + app_eui + ':' + dev_eui + ':*')
            msgs_down = db0.keys(ConstDB.msg_down + ConstDB.dev + dev_eui + ':*')
            mac_cmds = db0.keys(ConstDB.mac_cmd + dev_eui + ':*')
            trans_params = db0.keys(ConstDB.trans_params + dev_eui + ':*')
            groups = db0.keys(ConstDB.group_dev + '*:' + dev_eui)
            statistics_up = db0.keys(ConstDB.statistics_up + dev_eui + ':*')
            statistics_down = db0.keys(ConstDB.statistics_down + ConstDB.dev + dev_eui + ':*')
            pipe = db0.pipeline()
            pipe.delete(ConstDB.dev_ack + dev_eui)
            pipe.delete(ConstDB.dev + dev_eui)
            pipe.srem(ConstDB.app_devs + app_eui, self.dev_eui)
            for key in groups:
                pipe.delete(key)
            pipe.delete(ConstDB.addr + addr)
            pipe.delete(ConstDB.dev_gateways + dev_eui)
            for key in mac_cmds:
                pipe.delete(key)
            for key in msgs_up:
                pipe.delete(key)
            for key in msgs_down:
                pipe.delete(key)
            pipe.delete(ConstDB.que_down + ConstDB.dev + dev_eui)
            pipe.delete(ConstDB.mac_cmd_que + dev_eui)
            for key in trans_params:
                pipe.delete(key)
            for key in statistics_down:
                pipe.delete(key)
            for key in statistics_up:
                pipe.delete(key)
            pipe.execute()
            AddrManger.recycle_addr(unhexlify(addr))
        db_sql.session.commit()

    def __get_more_info(self):
        FREQ_PLAN = frequency_plan[self.app.freq_plan]
        info = db0.hget(ConstDB.dev_info + hexlify(self.dev_eui).decode(), self._info_field)
        self.MaxDutyCycle = int(info[0]) if info and info[0] else 0
        self.RX1DRoffset = int(info[1]) if info and info[1] else FREQ_PLAN.RX1DRoffset
        self.RX2DataRate = int(info[2]) if info and info[2] else FREQ_PLAN.RX2DataRate
        self.RX2Frequency = float(info[3]) if info and info[3] else FREQ_PLAN.RX2Frequency
        self.RxDelay = int(info[4]) if info and info[4] else FREQ_PLAN.RECEIVE_DELAY1
        self.battery = int(info[5]) if info and info[5] else None
        self.snr = int(info[6]) if info and info[6] else None

    def delete_mac_info(self):
        db0.delete(ConstDB.dev_info + hexlify(self.dev_eui).decode())

    def obj_to_dict(self):
        dd = {FieldDevice.name: self.name,
              FieldDevice.dev_eui: hexlify(self.dev_eui).decode(),
              FieldDevice.app_eui: hexlify(self.app_eui).decode(),
              FieldDevice.active_mode: self.active_mode.value,
              'freq_plan': self.app.freq_plan.value,}
        if self.join_device:
            dd[FieldDevice.appkey] = hexlify(self.join_device.appkey).decode()
        if self.active_at:
            dd[FieldDevice.active_at] = self.active_at.isoformat()
            dd[FieldDevice.addr] = hexlify(self.addr).decode()
            dd[FieldDevice.nwkskey] = hexlify(self.nwkskey).decode()
            dd[FieldDevice.appskey] = hexlify(self.appskey).decode()
            dd[FieldDevice.fcnt_up] = self.fcnt_up
            dd[FieldDevice.fcnt_down] = self.fcnt_down
            dd[FieldDevice.dev_class] = self.dev_class.value
            if self.dev_class == ClassType.b:
                dd[FieldDevice.datr] = self.datr
                dd[FieldDevice.periodicity] = self.periodicity
            dd[FieldDevice.adr] = self.adr
            dd[FieldDevice.check_fcnt] = self.check_fcnt
            dd['que_down'] = self.que_down.len()
            last_up_link = getattr(self.trans_status, 's_time', getattr(self.trans_status, 'time', None)) if self.trans_status else 'No Connection'
            if last_up_link == '':
                Logger.error(action=Action.get, resource=Resource.trans_params, id=self.dev_eui, msg=str(self.trans_params))
            dd['last_up_link'] = last_up_link
            dd[FieldInfo.MaxDutyCycle] = self.MaxDutyCycle
            dd[FieldInfo.RX1DRoffset] = self.RX1DRoffset
            dd[FieldInfo.RX2DataRate] = self.RX2DataRate
            dd[FieldInfo.RX2Frequency] = self.RX2Frequency
            dd[FieldInfo.RxDelay] = self.RxDelay
            dd[FieldInfo.battery] = self.battery
            dd[FieldInfo.snr] = self.snr
        return dd

    class objects:
        @classmethod
        def all(cls, group_id=None):
            """
            :param app_eui: bytes
            :return:
            """
            devices = []
            keys = []
            if group_id is not None:
                keys = db0.keys(ConstDB.group_dev + hexlify(group_id).decode() + ':*')
                keys = [unhexlify(key.decode().split(':')[2]) for key in keys]
            for key in keys:
                device = Device.query.get(key)
                devices.append(device)
            return devices


class JoinDevice(db_sql.Model):
    __tablename__ = 'join_device'

    dev_eui = Column(BINARY(8), ForeignKey(Device.dev_eui, ondelete='CASCADE', onupdate='CASCADE'), primary_key=True)
    appkey = Column(BINARY(16), unique=True, nullable=False)
    nwkkey = Column(BINARY(16), unique=True)
    ver = Column(Numeric(precision=2, scale=1), nullable=False, default=1.0)

    # device = relationship('Device', back_populates='join_device')
