from binascii import hexlify, unhexlify
from utils.db0 import db0, ConstDB0
from utils.exception import ReadOnlyDeny
from object.asserts import Assertions
from object.fields import ClassType, FieldDevice, TXParams
from object.que_down import QueDownDev
from object.application import Application
from frequency_plan import frequency_plan
from utils.log import Logger, Action, IDType

class ACKName:
    ack_request = 'ack_request'
    adr_ack_req = 'ADRACKReq'


class CheckFcnt:
    strict = 1
    relax = 0


class DeviceACK:
    def __init__(self, dev_eui, ack_name):
        self.dev_eui = dev_eui
        self.ack_name = ack_name

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise ReadOnlyDeny
        self.__dict__[key] = value

    def set(self, value):
        assert value == 0 or value == 1, 'ack_value ERROR'
        db0.hset(ConstDB0.dev_ack + hexlify(self.dev_eui).decode(), self.ack_name, value)

    def get(self):
        ack = db0.hget(ConstDB0.dev_ack + hexlify(self.dev_eui).decode(), self.ack_name)
        if ack is not None:
            return int(ack)
        else:
            return 0


class DevInfo:
    fields = ('MaxDutyCycle', 'RX1DRoffset', 'RX2DataRate', 'RX2Frequency', 'RxDelay', 'battery', 'SNR')

    def __init__(self, dev_eui):
        self.dev_eui = dev_eui
        self.key = ConstDB0.dev_info + hexlify(self.dev_eui).decode()

    # p means pre or possible. After Mac command sent. Value will set to be p.
    # c means confirmed. After Mac Command Answer received and is Success. P value will be set to C.
    def set_p_value(self, **kwargs):
        pipe = db0.pipeline()
        for name, value in kwargs.items():
            if name in DevInfo.fields:
                pipe.hset(self.key, 'p_' + name, value)
            else:
                Logger.error(action=Action.mac_cmd_send, type=IDType.dev_info, id=hexlify(self.dev_eui).decode(), msg='set_p_value unknow name:' % name)
                return
        pipe.execute()

    def p_to_c(self, *args):
        pipe = db0.pipeline()
        for arg in args:
            value = db0.hget(self.key, 'p_' + arg)
            if value is not None:
                pipe.hset(self.key, arg, value)
                pipe.hdel(self.key, 'p_' + arg)
            else:
                Logger.error(action=Action.mac_cmd_send, type=IDType.dev_info, id=hexlify(self.dev_eui).decode(), msg='No P value can be set to C: %s' % arg)
                return
        pipe.execute()

    def set_value(self, **kwargs):
        pipe = db0.pipeline()
        for name, value in kwargs.items():
            if name in DevInfo.fields:
                pipe.hset(self.key, name, value)
            else:
                Logger.error(action=Action.mac_cmd_get, type=IDType.dev_info, id=hexlify(self.dev_eui).decode(), msg='DevInfo set_value unknow name:' % name)
                return
        pipe.execute()


class Device:
    # fields = (FieldDevice.addr, FieldDevice.app_eui,
    #           FieldDevice.nwkskey, FieldDevice.appskey, FieldDevice.fcnt_up,
    #           FieldDevice.fcnt_down, FieldDevice.dev_class,
    #           FieldDevice.adr, FieldDevice.check_fcnt, FieldDevice.rx1dr_offset,)
    __vars_can_write = (FieldDevice.fcnt_up, FieldDevice.fcnt_down, FieldDevice.dev_class)
    __assert_switcher = {FieldDevice.dev_eui: Assertions.a_eui,
                         FieldDevice.addr: Assertions.a_addr,
                         FieldDevice.nwkskey: Assertions.a_nwkskey,
                         FieldDevice.appskey: Assertions.a_appskey,
                         FieldDevice.fcnt_up: Assertions.a_fcnt,
                         FieldDevice.fcnt_down: Assertions.a_fcnt,
                         FieldDevice.dev_class: Assertions.a_dev_class,
                         FieldDevice.adr: Assertions.a_bool,
                         FieldDevice.check_fcnt: Assertions.a_bool,
                         'que_down': QueDownDev.assert_isinstanceof,
                         'app': Application.assert_isinstanceof,
                         }

    __tx_params = (TXParams.RX1DRoffset, TXParams.RX2DataRate, TXParams.RX2Frequency, TXParams.RxDelay)

    def __init__(self, dev_eui, addr, app_eui, nwkskey, appskey=b'',
                 fcnt_up=0, fcnt_down=0, dev_class=ClassType.a,
                 adr=True, check_fcnt=True):
        """
        :param dev_eui: EUI-64 FORMAT 8bytes
        :param addr: 4 bytes
        :param app_eui: 16 hex string
        :param appskey: 16 bytes
        :param nwkskey: 16 bytes
        :return:
        """
        self.dev_eui = dev_eui
        self.addr = addr
        # self.app_eui = app_eui
        self.app = Application.objects.get(app_eui)
        self.appskey = appskey
        self.nwkskey = nwkskey
        self.fcnt_up = fcnt_up
        self.fcnt_down = fcnt_down
        self.dev_class = dev_class
        self.adr = adr
        self.check_fcnt = check_fcnt
        self.que_down = QueDownDev(self.dev_eui)

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in self.__vars_can_write:
                raise ReadOnlyDeny
        assert_method = self.__assert_switcher.get(key)
        if assert_method is not None:
            self.__assert_switcher[key](value)
        super.__setattr__(self, key, value)

    def update(self):
        db0.hmset(ConstDB0.dev + hexlify(self.dev_eui).decode(),
                  dict(zip(self.__vars_can_write,
                           (self.fcnt_up, self.fcnt_down,
                            self.dev_class.value))))

    # def get_user(self):
    #     user = db0.hget(ConstDB0.app + hexlify(self.app_eui).decode(), 'user_id')
    #     return int(user)

    def get_tx_params(self, name=None):
        FREQ_PLAN = frequency_plan[self.app.freq_plan]
        if name is None:
            info = db0.hmget(ConstDB0.dev_info + hexlify(self.dev_eui).decode(), self.__tx_params)
            tx_params = {}
            tx_params[TXParams.RX1DRoffset] = int(info[0]) if info and info[0] else FREQ_PLAN.RX1DRoffset
            tx_params[TXParams.RX2DataRate] = int(info[1]) if info and info[1] else FREQ_PLAN.RX2DataRate
            tx_params[TXParams.RX2Frequency] = float(info[2]) if info and info[2] else FREQ_PLAN.RX2Frequency
            tx_params[TXParams.RxDelay] = int(info[3]) if info and info[3] else FREQ_PLAN.RxDelay
            return tx_params
        elif name == TXParams.RxDelay:
            rxdelay = db0.hget(ConstDB0.dev_info + hexlify(self.dev_eui).decode(), TXParams.RxDelay)
            rxdelay = int(rxdelay) if rxdelay else FREQ_PLAN.RxDelay
            return rxdelay

    class objects:
        @staticmethod
        def get(dev_eui):
            """
            :param dev_eui: bytes
            :return:
            """
            Assertions.a_eui(dev_eui)
            info = db0.hgetall(ConstDB0.dev + hexlify(dev_eui).decode())
            Logger.info(info)
            try:
                addr = info[b'addr']
                app_eui = info[b'app_eui']
                nwkskey = info[b'nwkskey']
                appskey = info.get(b'appskey', b'')
                fcnt_up = int(info[b'fcnt_up'])
                fcnt_down = int(info[b'fcnt_down'])
                dev_class = ClassType(info[b'dev_class'].decode())
                adr = bool(int(info[b'adr']))
                check_fcnt = bool(int(info[b'check_fcnt']))
                return Device(dev_eui=dev_eui, addr=addr, app_eui=app_eui, nwkskey=nwkskey, appskey=appskey,
                              fcnt_up=fcnt_up, fcnt_down=fcnt_down, dev_class=dev_class, adr=adr,
                              check_fcnt=check_fcnt)
            except Exception as error:
                Logger.error(action=Action.object, type=IDType.device, id=hexlify(dev_eui).decode(), msg='Get Device ERROR: %s' % error)

        @staticmethod
        def get_dev_class(dev_eui):
            """
            :param dev_eui: bytes
            :return:
            """
            dev_class = db0.hget(ConstDB0.dev + hexlify(dev_eui).decode(), FieldDevice.dev_class)
            if dev_class is not None:
                dev_class = ClassType(dev_class.decode())
                return dev_class

        @classmethod
        def get_device_by_addr(cls, addr):
            """
            :param addr: bytes little endian
            :return:
            """
            key = db0.get(ConstDB0.addr + hexlify(addr).decode())
            if key is not None:
                key = key.decode().split(':')
                if key[0] == 'DEV':
                    return cls.get(unhexlify(key[1]))