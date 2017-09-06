from binascii import hexlify
from utils.db0 import db0, ConstDB0, Channel0
from object.fields import FieldDevice
from datetime import datetime
from utils.db2 import db2, ConstDB2
from utils.utils import bytes_to_hexstr
from utils.log import Logger, IDType, Action


class ConstMsg:
    ts = 'ts'
    fcnt = 'fcnt'
    port = 'port'
    data = 'data'
    freq = 'freq'
    rssi = 'rssi'
    lsnr = 'lsnr'
    datr = 'datr'
    cipher = 'cipher'
    nonce = 'nonce'
    gateways = 'gateways'

    EXPIRE_MSG = 7 * 86400
    EXPIRE_STATIS = 30 * 86400


class MsgDn:
    __redis_fields = (ConstMsg.fcnt, ConstMsg.datr,
                      ConstMsg.freq, ConstMsg.nonce)
    redis_fields = (ConstMsg.fcnt, ConstMsg.gateways)

    def __init__(self, category, eui, ts, fcnt, gateways, datr=None, freq=None, nonce=None):
        """
        :param eui: str
        :param ts: int
        :param fcnt: int
        :return:
        """
        assert category == ConstDB0.dev or category == ConstDB0.group, 'MsgDn category should be %s or %s, but %r got' % (
            ConstDB0.dev, ConstDB0.group, category)
        assert isinstance(
            fcnt, int), 'fcnt type should be int but %r got' % type(fcnt)
        assert isinstance(
            eui, str), 'eui type should be str but %r got' % type(eui)
        self.category = category
        self.eui = eui.lower()
        self.ts = ts
        self.fcnt = fcnt
        self.datr = datr
        self.freq = freq
        self.gateways = gateways

    def __obj_to_dict(self):
        dd = {}
        for key in self.__redis_fields:
            try:
                value = getattr(self, key)
                if value is not None:
                    dd[key] = value
            except AttributeError:
                pass
        return dd

    def save(self):
        try:
            app_eui = hexlify(
                db0.hget(self.category + self.eui, ConstDB0.app_eui)).decode()
        except TypeError as e:
            Logger.warning(action='MsgDn', type=IDType.app,
                           id=self.category + self.eui, msg=str(e))
            app_eui = self.eui.split(':')[0]

        key = ConstDB0.msg_down + self.category + \
            self.eui + ':' + str(round(self.ts))
        pipe = db0.pipeline()
        pipe.hmset(key, self.__obj_to_dict())
        pipe.expire(key, ConstMsg.EXPIRE_MSG)
        pipe.publish(Channel0.msg_alarm + app_eui, key)
        pipe.execute()
        self.__count_statistics_down()

        key = ConstDB2.dn_m + self.category + \
            self.eui + ':' + str(round(self.ts))
        pipe = db2.pipeline()
        info = {ConstMsg.fcnt: self.fcnt}
        if hasattr(self, ConstMsg.gateways):
            if isinstance(self.gateways, bytes):
                info[ConstMsg.gateways] = hexlify(self.gateways).decode()
            elif isinstance(self.gateways, list):
                info[ConstMsg.gateways] = ';'.join(
                    map(bytes_to_hexstr, self.gateways))
        pipe.hmset(key, info)
        pipe.expire(key, ConstMsg.EXPIRE_STATIS)
        pipe.publish(Channel0.dn_alarm + app_eui, key)
        pipe.execute()

    def __count_statistics_down(self):
        time_now = datetime.now()
        key = ConstDB0.statistics_down + self.category + \
            self.eui + ':' + time_now.strftime("%Y-%m-%d")
        pipe = db0.pipeline()
        pipe.hincrby(key, time_now.hour)
        pipe.expire(key, ConstMsg.EXPIRE_STATIS)
        pipe.execute()


class MsgUp:
    __redis_fields = (ConstMsg.fcnt, ConstMsg.data, ConstMsg.cipher, ConstMsg.port,
                      ConstMsg.rssi, ConstMsg.lsnr, ConstMsg.datr, ConstMsg.freq,)

    redis_fields = (ConstMsg.fcnt, ConstMsg.data,
                    ConstMsg.cipher, ConstMsg.port,)

    def __init__(self, dev_eui, ts, fcnt, port, data, cipher, mtype, retrans, trans_params, restart=False):
        """
        :param dev_eui: bytes
        :param ts: int
        :param fcnt: int
        :param port: int
        :param freq:
        :param dr:
        :param rssi:
        :param snr:
        :param data: bytes
        :return:
        """
        assert isinstance(cipher, bool), "MsgUp Decrypt Type Error"
        assert isinstance(ts, int), 'TS TYPE ERROR'
        assert isinstance(data, bytes), 'DATA TYPE ERROR'
        self.dev_eui = dev_eui
        self.ts = int(ts)
        self.fcnt = fcnt
        self.port = port
        self.data = data
        self.cipher = cipher.real
        self.mtype = mtype
        self.retrans = retrans.real
        for key, value in trans_params.items():
            setattr(self, key, value)
        self.restart = restart

    def __obj_to_dict(self):
        dd = {}
        for key in self.__redis_fields:
            try:
                value = getattr(self, key)
                if value is not None:
                    dd[key] = value
            except AttributeError:
                pass
        return dd

    def obj_to_dict(self):
        dd = {}
        for key in self.redis_fields:
            try:
                value = getattr(self, key)
                if value is not None:
                    dd[key] = value
            except AttributeError:
                pass
        return dd

    def save(self):
        """
        :param msg: MsgUp
        :return: None
        """
        dev_eui = hexlify(self.dev_eui).decode()
        app_eui = hexlify(db0.hget(ConstDB0.dev + dev_eui,
                                   FieldDevice.app_eui)).decode()
        key = ConstDB0.msg_up + app_eui + ':' + dev_eui + ':' + str(self.ts)
        pipe = db0.pipeline()
        pipe.hmset(key, self.__obj_to_dict())
        pipe.sadd(ConstDB0.mset + dev_eui, self.ts)
        pipe.expire(key, ConstMsg.EXPIRE_MSG)
        pipe.publish(Channel0.msg_alarm + app_eui, key)
        pipe.execute()
        self._count_statistics_up()

        pipe = db2.pipeline()
        if self.restart:
            cur_ts = self.ts
            pipe.rpush(ConstDB2.up_l_l + dev_eui, str(self.ts))
        else:
            cur_ts = db2.lindex(ConstDB2.up_l_l + dev_eui, -1)
            if cur_ts:
                cur_ts = int(cur_ts)
            else:
                cur_ts = self.ts
                pipe.rpush(ConstDB2.up_l_l + dev_eui, str(self.ts))
        pipe.rpush(ConstDB2.up_l + dev_eui + ':%s' % cur_ts, self.ts)
        key = ConstDB2.up_m + dev_eui + ':%s' % self.ts
        pipe.hmset(key, self.obj_to_dict())
        pipe.expire(key, ConstMsg.EXPIRE_STATIS)
        Logger.info('fuming', Channel0.up_alarm + app_eui)
        pipe.publish(Channel0.up_alarm + app_eui, key)
        pipe.execute()

    def _count_statistics_up(self):
        """
        :param eui: DEV:hex string or GROUP:hex string
        :return:
        """
        time_now = datetime.now()
        pipe = db0.pipeline()
        key = ConstDB0.statistics_up + \
            hexlify(self.dev_eui).decode() + ':' + \
            time_now.strftime("%Y-%m-%d")
        pipe.hincrby(key, time_now.hour)
        pipe.expire(key, ConstMsg.EXPIRE_STATIS)
        if self.retrans:
            key = ConstDB0.statistics_retrans + \
                hexlify(self.dev_eui).decode() + ':' + \
                time_now.strftime("%Y-%m-%d")
            pipe.hincrby(key, time_now.hour)
            pipe.expire(key, ConstMsg.EXPIRE_STATIS)
        pipe.execute()
