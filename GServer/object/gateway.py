from utils.db0 import db0, ConstDB0
from utils.db3 import db3, ConstDB3
from utils.db4 import db4, ConstDB4, Channel4
from binascii import hexlify
from utils.exception import ReadOnlyDeny
from object.asserts import Assertions
from frequency_plan import FrequencyPlan
from datetime import datetime
from utils.log import Logger, Action, IDType
from const import Const
from config import ISIPV6

"""
 Name |  Type  | Function
:----:|:------:|--------------------------------------------------------------
 time | string | UTC 'system' time of the gateway, ISO 8601 'expanded' format
 lati | number | GPS latitude of the gateway in degree (float, N is +)
 long | number | GPS latitude of the gateway in degree (float, E is +)
 alti | number | GPS altitude of the gateway in meter RX (integer)
 rxnb | number | Number of radio packets received (unsigned integer)
 rxok | number | Number of radio packets received with a valid PHY CRC
 rxfw | number | Number of radio packets forwarded (unsigned integer)
 ackr | number | Percentage of upstream datagrams that were acknowledged
 dwnb | number | Number of downlink datagrams received (unsigned integer)
 txnb | number | Number of packets emitted (unsigned integer)
"""


class FieldGateway:
    mac_addr = 'mac_addr'
    user_id = 'user_id'
    public = 'public'
    disable = 'disable'
    freq_plan = 'freq_plan'
    lng = 'lng'
    lat = 'lat'
    alt = 'alt'
    location = 'location'


class FieldPullInfo:
    ip_addr = 'ip_addr'
    prot_ver = 'prot_ver'


class Location:
    _assert_switcher = {FieldGateway.lng: Assertions.a_float,
                        FieldGateway.lat: Assertions.a_float,
                        FieldGateway.alt: Assertions.a_int, }

    def __setattr__(self, key, value):
        self._assert_switcher[key](value)
        self.__dict__[key] = value

    def __init__(self, lng, lat, alt):
        self.lng = lng
        self.lat = lat
        self.alt = alt

    def __str__(self):
        # return '%.4f,%.4f,%i' % (self.lng, self.lat, self.alt)
        return '%s,%s,%s' % (self.lng, self.lat, self.alt)

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(
            value, Location), '%r is not a valid Location' % value

    class objects:

        @staticmethod
        def str_to_obj(string):
            string = string.split(',')
            try:
                return Location(float(string[0]), float(string[1]), int(string[2]))
            except Exception as error:
                raise error


class GatewayStatus:

    def __init__(self, mac_addr, lati, long, alti):
        self.mac_addr = mac_addr
        self.location = Location(lng=long, lat=lati, alt=alti)

    def save(self):
        db0.hset(ConstDB0.gateway + hexlify(self.mac_addr).decode(),
                 FieldGateway.location, str(self.location))
        db4.publish(Channel4.gis_gateway_location +
                    hexlify(self.mac_addr).decode(), str(self.location))


class Gateway:
    fields = (FieldGateway.user_id, FieldGateway.freq_plan,
              FieldGateway.public, FieldGateway.disable)
    __assert_switcher = {FieldGateway.mac_addr: Assertions.a_eui,
                         FieldGateway.user_id: Assertions.a_not_negative_int,
                         FieldGateway.public: Assertions.a_bool,
                         FieldGateway.disable: Assertions.a_bool,
                         FieldGateway.freq_plan: FrequencyPlan.assert_isinstanceof,
                         }

    def __init__(self, mac_addr, user_id, freq_plan, public, disable=0):
        self.mac_addr = mac_addr
        self.user_id = user_id
        self.freq_plan = freq_plan
        self.public = public
        self.disable = disable

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise ReadOnlyDeny
        self.__assert_switcher[key](value)
        self.__dict__[key] = value

    def __eq__(self, other):
        return self.mac_addr == other.mac_addr

    def __hash__(self):
        return hash(self.mac_addr)

    def set_time(self, now):
        now = int(now)
        hex_mac_addr = hexlify(self.mac_addr).decode()
        last = db3.get(ConstDB3.T_GATEWAY + hex_mac_addr)
        last = int(last) if last else 0
        db3.set(ConstDB3.T_GATEWAY + hex_mac_addr, now)
        if now - last > Const.CONNECTION_TIMEOUT:
            db3.rpush(ConstDB3.P_GATEWAY +
                      hexlify(self.mac_addr).decode(), last, now)

    def pop_restart(self):
        restart = db0.hget(ConstDB0.gateway +
                           hexlify(self.mac_addr).decode(), 'restart')
        if restart == b'1':
            db0.hdel(ConstDB0.gateway +
                     hexlify(self.mac_addr).decode(), 'restart')
            Logger.info(action=Action.object, type=IDType.gateway,
                        id=hexlify(self.mac_addr).decode(), msg='Restart')
            return True
        else:
            return False

    def request2niot_platform(self):
        """
        The function is used to publish message to program which will send request to niot platform about the gateway.
        :return:
        """
        db0.publish(ConstDB0.niot_request, hexlify(self.mac_addr))

    def frequency_statistics(self, freq_plan):
        """
        :param eui: DEV:hex string or GROUP:hex string
        :return:
        """
        time_now = datetime.now()
        key = ConstDB0.statistics_freq + hexlify(self.mac_addr).decode(
        ) + ':' + time_now.strftime("%Y-%m-%d") + ':' + str(time_now.hour)
        pipe = db0.pipeline()
        pipe.hincrby(key, freq_plan)
        pipe.expire(key, 30 * 86400)
        pipe.execute()

    class objects:

        @staticmethod
        def get(mac_addr):
            info = db0.hmget(ConstDB0.gateway +
                             hexlify(mac_addr).decode(), Gateway.fields)
            try:
                user_id = int(info[0])
                freq_plan = FrequencyPlan(info[1].decode())
                public = bool(int(info[2]))
                disable = bool(int(info[3]))
                return Gateway(mac_addr, user_id, freq_plan, public, disable)
            except Exception as error:
                Logger.error(action=Action.object, type=IDType.gateway, id=hexlify(
                    mac_addr).decode(), msg='Get Gateway ERROR: %s' % error)
                return None

        @classmethod
        def list_order_by_score(cls, dev_eui):
            """
            :param dev_eui: bytes
            :return:
            """
            key_list = db0.zrevrange(
                ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 0, -1)
            gateway_list = []
            for mac_addr in key_list:
                gateway_list.append(cls.get(mac_addr))
            return gateway_list

        @staticmethod
        def best_mac_addr(dev_eui):
            key_list = db0.zrevrange(
                ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 0, 0)
            if len(key_list) > 0:
                return key_list[0]
            else:
                return None


class PullInfo:

    def __init__(self, mac_addr, ip_addr, prot_ver):
        """
        :param mac_addr: bytes
        :param ip_addr: tuple
        :param prot_ver: int
        :return:
        """
        self.mac_addr = mac_addr
        self.ip_addr = ip_addr
        self.prot_ver = prot_ver

    class objects:

        @classmethod
        def get_pull_info(cls, mac_addr):
            key = ConstDB0.gateway_pull + hexlify(mac_addr).decode()
            info = db0.hgetall(key)
            try:
                ip_addr = PullInfo.ip_addr_str_to_tuple(
                    info[b'ip_addr'].decode())
                prot_ver = int(info[b'prot_ver'])
                return PullInfo(mac_addr, ip_addr, prot_ver)
            except Exception as error:
                Logger.error(action=Action.object,
                             type=IDType.pull_info, id=key, msg=str(error))

    def save(self):
        ip_addr = self.ip_addr_tuple_to_str(self.ip_addr)
        db0.hmset(ConstDB0.gateway_pull + hexlify(self.mac_addr).decode(),
                  {FieldPullInfo.ip_addr: ip_addr, FieldPullInfo.prot_ver: self.prot_ver})

    @staticmethod
    def ip_addr_tuple_to_str(tuple_addr):
        if tuple_addr[0][0:7] == '::ffff:':
            tuple_addr = list(tuple_addr)
            tuple_addr[0] = tuple_addr[0][7:]
            tuple_addr = tuple(tuple_addr)
        if isinstance(tuple_addr, tuple):
            return '%s:%s' % (tuple_addr[0], tuple_addr[1])
        else:
            raise TypeError('Except tuple but got %s' % tuple_addr)

    @staticmethod
    def ip_addr_str_to_tuple(str_addr):
        tuple_addr = str_addr.split(':')
        if ISIPV6:
            tuple_addr[0] = '::ffff:' + tuple_addr[0]
        tuple_addr[1] = int(tuple_addr[1])
        return tuple(tuple_addr)
