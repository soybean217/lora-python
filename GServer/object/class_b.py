# cacluate the UTC, pingoffset, ping_period
import math
from utils.lora_crypto import LoRaCrypto
from object.asserts import Assertions
from object.fields import FieldDevice, TXParams
from object import TransParams, DevGateway
from utils.db0 import db0, ConstDB0
from utils.exception import ReadOnlyDeny
from utils.log import logger, ConstLog
from utils.utils import iso_to_utc_ts


class BConst:
    # beacon time parameter
    BEACON_PERIOD = 128         # unit:s; fixed to 128s;
    BEACON_RESERVED = 2.120     # unit:s; device recv the beacon from gateway:2.120s
    BEACON_GUARD = 3.000        # unit:s; 3.000s
    BEACON_WINDOW = 122.880     # unit:s; 122.880s
    TBEACON_DELAY = 0		# uint:s; that is number 1.5ms +/- 1uSec delay.
    NWKID = 22
    # ping slot
    SLOT_LEN = 0.03           # unit:s; fixed to 30ms, unit of ping slot period
    NETWORK_DELAY = 0.1     # unit:s; can be change to other value;default as 100ms
    KEY = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'


class ClassBInfo:
    __vars_can_write = ('datr', 'periodicity')
    fields = ('datr', 'periodicity')
    __assert_switcher = {'eui': Assertions.a_group_dev_eui,
                         'datr': Assertions.a_not_negative_int,
                         'periodicity': Assertions.a_not_negative_int, }

    def __init__(self, eui, datr, periodicity):
        """
        :param eui: str GROUP:...:... or DEV:...
        :param datr: int from 0 - 7
        :param periodicity: int from 0-6
        :return:
        """
        self.eui = eui
        self.datr = datr
        self.periodicity = periodicity

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in self.__vars_can_write:
                raise ReadOnlyDeny
        self.__assert_switcher[key](value)
        self.__dict__[key] = value

    def set(self):
        db0.hmset(ConstDB0.class_b + self.eui,
                  dict(zip(self.__vars_can_write,
                           (self.datr, self.periodicity))))

    class objects:
        @staticmethod
        def get(eui):
            info = db0.hmget(ConstDB0.class_b + eui, ClassBInfo.fields)
            try:
                datr = info[0]
                if datr is not None:
                    datr = int(datr)
                else:
                    datr = 0
                periodicity = info[1]
                if periodicity is not None:
                    periodicity = int(periodicity)
                else:
                    periodicity = 0
                return ClassBInfo(eui, datr=datr, periodicity=periodicity)
            except Exception as error:
                logger.error(ConstDB0.class_b + ' %r' % error)
                return None


class DNTime:
    fields = ('beacon_num', 'ping_slot_num', 'ping_offset')
    __vars_can_write = ('beacon_num', 'ping_slot_num', 'ping_offset')
    __assert_switcher = {'eui': Assertions.a_group_dev_eui,
                         'beacon_num': Assertions.a_not_negative_int,
                         'ping_slot_num': Assertions.a_not_negative_int,
                         'ping_offset': Assertions.a_not_negative_int, }

    def __init__(self, eui, beacon_num, ping_slot_num, ping_offset):
        """
        :param eui: str GROUP:... or DEV:...
        :param beacon_num: int
        :param ping_slot_num: int
        :param ping_offset: int
        :return:
        """
        self.eui = eui
        self.beacon_num = beacon_num
        self.ping_slot_num = ping_slot_num
        self.ping_offset = ping_offset

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in self.__vars_can_write:
                raise ReadOnlyDeny
        self.__assert_switcher[key](value)
        self.__dict__[key] = value

    def update(self):
        db0.hmset(ConstDB0.b_time + self.eui,
                  dict(zip(self.__vars_can_write,
                           (self.beacon_num, self.ping_slot_num, self.ping_offset))))

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, DNTime), '%r is not instance of DNTime' % value

    class objects:
        @staticmethod
        def get(eui):
            """
            :param eui: str GROUP:... or DEV:...
            :return:
            """
            dn_time = None
            info = db0.hmget(ConstDB0.b_time + eui, DNTime.fields)
            try:
                dn_time = DNTime(eui, int(info[0]), int(info[1]), int(info[2]))
            except AssertionError as error:
                logger.error(ConstLog.class_b + '%r' % error)
                return None
            except Exception as error:
                logger.error(ConstLog.class_b + ' %r' % error)
            finally:
                if dn_time is None:
                    dn_time = DNTime(eui, 0, 0, 0)
                return dn_time


class BeaconTiming:

    @staticmethod
    def cal_beacon_time(beacon_num):
        """
        :param beacon_num: int
        :return: float
        """
        t = (beacon_num * BConst.BEACON_PERIOD + BConst.TBEACON_DELAY + BConst.NWKID)
        return t

    @staticmethod
    def cal_beacon_num(ts):
        """
        :param ts: utc timestamp int or float
        :return: int
        """
        k = int((ts - BConst.TBEACON_DELAY - BConst.NWKID) / BConst.BEACON_PERIOD)
        return k

    @classmethod
    def cal_beacon_time_next(cls, ts):
        """
        :param ts: int
        :return:
        """
        beacon_num = cls.cal_beacon_num(ts) + 1
        beacon_time = cls.cal_beacon_time(beacon_num)
        if beacon_time - ts < 0:   # may not be 0, may be a number that represent Network transmission Delay
            beacon_num += 1
            beacon_time = cls.cal_beacon_time(beacon_num)
        return beacon_time

    @classmethod
    def cal_beacon_time_delay(cls, device):
        """
        :param ts: int
        :return:
        """
        mac_addr = DevGateway.get_best_mac_addr(device.dev_eui)
        time = TransParams.objects.get(device.dev_eui, mac_addr, 'time')
        ts = iso_to_utc_ts(time)
        DevGateway.set_best(device.dev_eui, mac_addr)
        rxdelay = device.get_tx_params(TXParams.RxDelay)
        ts = ts + rxdelay
        beacon_time = cls.cal_beacon_time_next(ts)
        delay = int((beacon_time - ts) * 1000 / 30)
        return delay


class BTiming:
    __vars_can_write = ()
    __assert_switcher = {'eui': Assertions.a_group_dev_eui,
                         'ts': Assertions.a_positive_num,
                         'ping_nb': Assertions.a_positive_int,
                         'ping_period': Assertions.a_not_negative_int,
                         'datr': Assertions.a_not_negative_int,
                         'dntime': DNTime.assert_isinstanceof,
                         }

    def __init__(self, eui, ts):
        """
        :param eui: str GROUP:... or DEV:...
        :param ts:
        :return:
        """
        self.eui = eui
        class_b_info = ClassBInfo.objects.get(eui)
        self.ping_nb = pow(2, 7-class_b_info.periodicity)   # ping_nb = 2^(7-periodicity)
        self.ping_period = pow(2, 5 + class_b_info.periodicity)     # ping_period = 2^12/ping_nb = 2^(12-(7-periodicity)) = 2^(5+periodicity)
        self.datr = class_b_info.datr
        self.ts = ts
        self.dntime = DNTime.objects.get(eui)

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in self.__vars_can_write:
                raise ReadOnlyDeny
        self.__assert_switcher[key](value)
        self.__dict__[key] = value

    def cal_ping_offset(self, beacon_time):
        """
        :param beacon_time: int or float
        :param addr: bytes
        :param ping_period: int
        :return: int
        """
        addr = db0.hget(self.eui, FieldDevice.addr)
        addr = int.from_bytes(addr, byteorder='big')
        rand = LoRaCrypto.ping_rand_compute(BConst.KEY, int(beacon_time), addr)
        return (rand[0] + rand[1] * 256) % self.ping_period
        # return (rand[0] + rand[1] * 256) % self.ping_period

    def ping_time(self):
        """
        :return:
        """
        beacon_num = BeaconTiming.cal_beacon_num(self.ts)
        logger.info(ConstLog.class_b + self.eui + 'start ping_nb:%s, ping_period:%s, now:%s, beacon_num:%s, dntime:{ping_slot_num: %s, ping_offset: %s, beacon_num: %s}'
                    % (self.ts, self.ping_nb, self.ping_period, beacon_num, self.dntime.ping_slot_num, self.dntime.ping_offset, self.dntime.beacon_num))
        if beacon_num < self.dntime.beacon_num:
            if self.dntime.ping_slot_num < (self.ping_nb - 1):
                beacon_time = BeaconTiming.cal_beacon_time(self.dntime.beacon_num)
                self.dntime.ping_slot_num += 1
            else:
                self.dntime.beacon_num += 1
                beacon_time = BeaconTiming.cal_beacon_time(self.dntime.beacon_num)
                self.dntime.ping_slot_num = 0
                self.dntime.ping_offset = self.cal_ping_offset(beacon_time)
            self.dntime.update()
        elif beacon_num == self.dntime.beacon_num:
            beacon_time = BeaconTiming.cal_beacon_time(self.dntime.beacon_num)
            sub_time = self.ts - beacon_time
            ping_offset = self.cal_ping_offset(beacon_time)
            ping_slot_num = math.ceil((
                                math.ceil((sub_time - BConst.BEACON_RESERVED) / BConst.SLOT_LEN) -
                                ping_offset) / self.ping_period)
            if ping_slot_num < self.ping_nb and self.dntime.ping_slot_num < (self.ping_nb - 1):
                if ping_slot_num <= self.dntime.ping_slot_num:
                    self.dntime.ping_slot_num += 1
                else:
                    self.dntime.ping_slot_num = ping_slot_num
            else:
                self.dntime.beacon_num += 1
                beacon_time = BeaconTiming.cal_beacon_time(self.dntime.beacon_num)
                self.dntime.ping_offset = self.cal_ping_offset(beacon_time)
                self.dntime.ping_slot_num = 0
            self.dntime.update()
        else:   # (self.dntime is not None and beacon_num >= self.dntime.beacon_num) or (self.dntime is None)
            self.dntime.beacon_num = beacon_num
            beacon_time = BeaconTiming.cal_beacon_time(self.dntime.beacon_num)
            sub_time = self.ts - beacon_time
            self.dntime.ping_offset = self.cal_ping_offset(beacon_time)
            self.ping_slot_num = math.ceil((
                                math.ceil((sub_time - BConst.BEACON_RESERVED) / BConst.SLOT_LEN) -
                                self.dntime.ping_offset) / self.ping_period)
            if self.ping_slot_num >= self.ping_nb:
                self.dntime.beacon_num += 1
                beacon_time = BeaconTiming.cal_beacon_time(self.dntime.beacon_num)
                self.dntime.ping_offset = self.cal_ping_offset(beacon_time)
                self.dntime.ping_slot_num = 0
            self.dntime.update()
            logger.info(ConstLog.class_b + self.eui + 'end ping_nb:%s, ping_period:%s, now:%s, beacon_num:%s, dntime:{ping_slot_num: %s, ping_offset: %s, beacon_num: %s}'
                        % (self.ts, self.ping_nb, self.ping_period, beacon_num, self.dntime.ping_slot_num, self.dntime.ping_offset, self.dntime.beacon_num))
        return self.cal_ping_slot_time(beacon_time, self.dntime.ping_offset, self.dntime.ping_slot_num, self.ping_period)

    @staticmethod
    def cal_ping_slot_time(beacon_time, ping_offset, ping_slot_num, ping_period):
        ping_slot_time = beacon_time + BConst.BEACON_RESERVED + (ping_offset + ping_slot_num * ping_period) * BConst.SLOT_LEN
        return ping_slot_time


   # now:1482737160.7241452, beacon_num:11583883, dntime:{ping_slot_num: 98, ping_offset: 0, beacon_num: 11583883
   #  2016-12-26T07:25:42.199999Z

if __name__ == '__main__':
    beacon_num = 11583883
    beacon_time = BeaconTiming.cal_beacon_time(beacon_num)
    ping_offset = 0
    ping_period = 32
    ping_slot_num = 98
    ts = 1482737160.7241452
    sub_time = ts - beacon_time
    print('sub_time', sub_time)
    a = math.ceil((math.ceil((sub_time - BConst.BEACON_RESERVED) / BConst.SLOT_LEN) - ping_offset) / ping_period)
    print(a)
    # a = BTiming.cal_ping_slot_time(BeaconTiming.cal_beacon_time(beacon_num), ping_offset, ping_period, ping_slot_num)
    # print(a)
    # ts = datetime.utcfromtimestamp(a)
    # print(ts)
# if __name__ == '__main__':
#      from time import time
#      import requests
#      from binascii import unhexlify
#      dev_eui = '3938383157358916'
#      response = requests.get('https://api-lorawan.cniotroot.cn/devices/3938383157358916', auth=('zhangjiayi@niot.cn','lw123456'))
#      info = response.json()
#      db0.hmset(ConstDB0.dev + dev_eui, {'addr':unhexlify(info['addr']), 'app_eui':unhexlify(info['app_eui']), 'check_fcnt':info['check_fcnt'].real,
#                                         'fcnt_up':info['fcnt_up'],'nwkskey':info[''],'fcnt_down':info, adr, appskey, dev_class})
#      # from binascii import unhexlify
#      # b_time = BTiming(eui='DEV:3938383157358916', ts=time())
#      # ts = b_time.ping_time()
#      # tt = datetime.utcfromtimestamp(ts).isoformat() + 'Z'
#      # print(ts, tt)