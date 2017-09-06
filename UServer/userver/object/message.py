from database.db0 import db0, ConstDB, Channel
from binascii import hexlify
from utils.utils import display_hex
import time
from utils.log import logger


class ConstMsg:
    cmd = 'cmd'
    eui = 'EUI'

    port = 'port'
    encdata = 'encdata'
    data = 'data'
    success = 'success'
    error = 'error'
    seqdn = 'seqdn'
    filter = 'filter'
    start_ts = 'start_ts'
    end_ts = 'end_ts'
    page_num = 'page_num'
    per_page = 'per_page'
    total = 'total'
    cache = 'cache'
    dev_eui = 'dev_eui'
    app_eui = 'app_eui'
    name = 'name'
    dev_addr = 'dev_addr'
    nwkskey = 'nwkskey'
    seqno = 'seqno'
    group_id = 'group_id'


class ConstCmd:
    rx = 'rx'
    txd = 'txd'
    mtxd = 'mtxd'
    tx = 'tx'
    mtx = 'mtx'
    cq = 'cq'


class FieldMsg:
    freq = 'freq'
    datr = 'datr'
    rssi = 'rssi'
    lsnr = 'lsnr'
    port = 'port'
    encrypt = 'encrypt'
    data = 'data'
    fcnt = 'fcnt'
    ts = 'ts'
    cipher = 'cipher'


class Msg(object):
    def __init__(self, app_eui):
        assert isinstance(app_eui, bytes) and len(app_eui)==8, 'APP_EUI TYPE ERROR'
        self.app_eui = app_eui
        self.ps = db0.pubsub()

    def listen_msg_alarm(self):
        self.ps.subscribe(Channel.msg_alarm + hexlify(self.app_eui).decode())
        return self.ps

    def stop_listen(self):
        if hasattr(self, 'ps'):
            self.ps.unsubscribe(Channel.msg_alarm + hexlify(self.app_eui).decode())


class MsgUp(object):
    def __init__(self, dev_eui, ts, fcnt, port, freq, datr, rssi, snr, cipher, data=None):
        """
        :param dev_eui: bytes
        :param ts: int
        :param fcnt: int
        :param port: int
        :param freq: str
        :param dr: str
        :param rssi: str
        :param snr: str
        :param data: bytes
        :param encdata: bytes
        :return:
        """
        # assert isinstance(encrypt, bool), "MsgUp Decrypt Type Error"
        assert isinstance(data, bytes), 'DATA TYPE ERROR'
        self.dev_eui = dev_eui
        self.ts = int(ts)
        self.fcnt = fcnt
        self.port = port
        self.freq = freq
        self.datr = datr
        self.rssi = rssi
        self.snr = snr
        self.data = data
        self.cipher = cipher

    def post_rx(self):
        dd = {ConstMsg.eui: display_hex(self.dev_eui),
              FieldMsg.ts: self.ts,
              FieldMsg.fcnt: self.fcnt,
              FieldMsg.port: self.port,
              FieldMsg.freq: self.freq,
              FieldMsg.datr: self.datr,
              FieldMsg.rssi: self.rssi,
              FieldMsg.lsnr: self.snr,
              FieldMsg.cipher: self.cipher,
              FieldMsg.data: display_hex(self.data) if self.data else ''}
        return dd

    def obj_to_dict(self):
        dict = {ConstMsg.eui: display_hex(self.dev_eui),
                FieldMsg.ts: self.ts,
                FieldMsg.fcnt: self.fcnt,
                FieldMsg.port: self.port,
                FieldMsg.freq: self.freq,
                FieldMsg.datr: self.datr,
                FieldMsg.rssi: self.rssi,
                FieldMsg.lsnr: self.snr,
                FieldMsg.cipher: self.cipher,
                FieldMsg.data: display_hex(self.data) if self.data else ''}
        return dict

    class objects:
        @staticmethod
        def get(msg_key):
            """
            :param msg_key: str
            :return:
            """
            info = db0.hgetall(msg_key)
            try:
                msg_key = msg_key.split(':')
                dev_eui = msg_key[2]
                ts = msg_key[3]
                fcnt = int(info[b'fcnt'])
                port = int(info[b'port'])
                freq = info[b'freq'].decode()
                datr = info.get(b'dr')
                if not datr:
                    datr = info.get(b'datr')
                datr = datr.decode()
                rssi = info[b'rssi'].decode()
                snr = info.get(b'snr')
                if not snr:
                    snr = info.get(b'lsnr')
                snr = snr.decode()
                cipher = info.get(b'cipher')
                if cipher is not None:
                    cipher = bool(int(cipher))
                data = info.get(b'encdata')
                if data is not None:
                    cipher = True
                else:
                    data = info.get(b'data')
                    cipher = cipher if cipher is not None else False
                return MsgUp(dev_eui=dev_eui, ts=ts, fcnt=fcnt, port=port, freq=freq, datr=datr, rssi=rssi, snr=snr, cipher=cipher, data=data)
            except KeyError:
                pass

        @classmethod
        def all(cls, app_eui, dev_eui=None, start_ts=0, end_ts=-1, cur_cnt=None):
            """
            :param app_eui: bytes
            :param dev_eui: bytes
            :param start_ts: int
            :param end_ts: int
            :param cur_cnt: int
            :return:
            """
            if dev_eui is None:
                dev_eui = '*'
            else:
                dev_eui = hexlify(dev_eui).decode()
            app_eui = hexlify(app_eui).decode()
            keys = db0.keys(ConstDB.msg_up + app_eui + ':' + dev_eui + ':*')
            # logger.debug('WHY NO MSG SHOW' + 'KEYS LENGTH: %d' % len(keys))
            msgs = []
            filted_keys = []
            for key in keys:
                key = key.decode()
                ts = int(key.split(':')[3])
                if start_ts < ts and ((end_ts < 0) or (ts < end_ts)):
                    filted_keys.append(key)

                # else:
                #     logger.debug('WHY NO MSG SHOW' + 'MSGS BE FILTERED: %s' % key)
            filted_keys.sort(key=lambda x: x.split(':')[3], reverse=True)
            if cur_cnt and cur_cnt < len(filted_keys):
                print(cur_cnt)
                filted_keys = filted_keys[0: cur_cnt]
            for key in filted_keys:
                msg = MsgUp.objects.get(key)
                if msg:
                    msgs.append(msg)
            return msgs

        # @classmethod
        # def all_dict(cls, app_eui, dev_eui=None, start_ts=0, end_ts=-1):
        #     all_msg = cls.all(app_eui, dev_eui, start_ts, end_ts)


class MsgDn:
    def __init__(self, type, eui, ts, fcnt, data=None):
        """
        :param type:
        :param eui: bytes
        :param ts: int
        :param fcnt: int
        :param data: bytes
        :return:
        """
        assert type == 'GROUP' or type == 'DEV', 'MSG_DOWN TYPE ERROR'
        self.type = type
        self.eui = eui
        self.ts = int(ts)
        self.fcnt = fcnt
        if data is None:
            self.data = b''
        else:
            self.data = data

    def confirm_tx(self):
        dd = {ConstMsg.cmd: ConstCmd.txd,
              ConstMsg.eui: display_hex(self.eui),
              FieldMsg.ts: self.ts,
              FieldMsg.fcnt: self.fcnt,}
        return dd

    def obj_to_dict(self):
        dd = {ConstMsg.dev_eui if self.type == 'DEV' else ConstMsg.group_id: display_hex(self.eui),
              FieldMsg.ts: self.ts,
              ConstMsg.data: display_hex(self.data),
              FieldMsg.fcnt: self.fcnt, }
        return dd

    class objects:
        @staticmethod
        def get(msg_key):
            """
            :param msg_key: str
            :return:
            """
            info = db0.hgetall(msg_key)
            if len(info) > 0:
                msg_key = msg_key.split(':')
                type = msg_key[1]
                if type == 'DEV':
                    eui = msg_key[2]
                    ts = msg_key[3]
                elif type == 'GROUP':
                    eui = msg_key[3]
                    ts = msg_key[4]
                fcnt = int(info[b'fcnt'])
                data = info[b'data']
                return MsgDn(type=type, eui=eui, ts=ts, fcnt=fcnt, data=data)

        @classmethod
        def all(cls, type=None, eui=None, start_ts=0, end_ts=-1):
            """
            :param app_eui: bytes
            :param dev_eui: bytes
            :param group_id: bytes
            :param start_ts: int
            :param end_ts: int
            :return:
            """
            assert type == 'GROUP' or type == 'DEV', 'MSG_DOWN TYPE ERROR'
            if end_ts == -1:
                end_ts = int(time.time())
            if eui is None:
                eui = '*'
            else:
                eui = hexlify(eui).decode()
            if type is None:
                type = '*'
            keys = db0.keys(ConstDB.msg_down + type + ':' + eui + ':*')
            # logger.debug('WHY NO MSG SHOW' + 'KEYS LENGTH: %d' % len(keys))
            msgs = []
            for key in keys:
                key = key.decode()
                ts = int(key.split(':')[3])
                if start_ts < ts < end_ts:
                    msg = cls.get(key)
                    msgs.append(msg)
                else:
                    logger.debug('WHY NO MSG SHOW' + 'MSGS BE FILTERED: %s' % key)
            return msgs