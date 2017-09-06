from abc import ABCMeta, abstractmethod
from struct import pack
from binascii import hexlify
from database.db0 import db0, ConstDB, Channel
from userver.object.const import FieldDevice, ClassType, FieldGroup, MAX_FRMPAYLOAD_LENGTH
from utils.log import Logger, Action, Resource
from utils.errors import AppSKeyAbsence, SeqNoError, QueOccupied


class QueDown(metaclass=ABCMeta):
    @abstractmethod
    def push(self, fport, payload, cipher):
        pass

    @abstractmethod
    def len(self):
        pass

    @abstractmethod
    def clear(self):
        pass


class QueDownGroup(QueDown):
    def __init__(self, app_eui, id, que_limit=1):
        """
        :param app_eui: bytes
        :param id: bytes
        :return:
        """
        app_eui = hexlify(app_eui).decode()
        if not db0.sismember(ConstDB.app_groups+app_eui, id):
            raise KeyError("Data enqueue failed. Group %s not registered in this app %s" % (hexlify(id).decode(), app_eui))
        key = ConstDB.group + hexlify(id).decode()
        self.id = id
        self.key = key
        self.que_limit = que_limit

    def push(self, fport, payload, cipher=False, seqno=None):
        """
        :param fport: int from 0 to 255
        :param payload: bytes
        :param cipher: True or False
        :param seqno: if cipher is True, seqno mush present and must math fcnt else will raise SeqNoError
        :return:
        """
        assert isinstance(payload, bytes) and len(payload) < MAX_FRMPAYLOAD_LENGTH, 'Payload Error'
        assert isinstance(fport, int) and 0 < fport < 255, 'FPort Error'
        assert isinstance(cipher, bool), 'Cipher Type Error'
        if self.que_limit <= self.len():
            raise QueOccupied('The queue of this Group:%s is occupied' % hexlify(self.id).decode())
        fport = pack('B', fport)
        if cipher is False:
            appskey = db0.hget(self.key, FieldGroup.appskey)
            if len(appskey) != 16:
                raise AppSKeyAbsence(self.key)
            cipher = b'\x00'
        else:
            fcnt = int(db0.hget(self.key, FieldGroup.fcnt))
            que_len = self.len()
            seqno_expect = fcnt + que_len + 1
            if seqno != seqno_expect:
                raise SeqNoError(seqno, seqno_expect)
            cipher = b'\x01'
        db0.rpush(ConstDB.que_down + self.key, cipher + fport + payload)
        db0.publish(Channel.que_down_alarm_multi, self.key)
        Logger.info(action=Action.publish, resource=Resource.group, id=self.id, msg='Publish ' + Channel.que_down_alarm_multi + ' ' + self.key)

    def len(self):
        return db0.llen(ConstDB.que_down + self.key)

    def clear(self):
        return db0.delete(ConstDB.que_down + self.key)


class QueDownDev(QueDown):
    def __init__(self, dev_eui, app_eui=None, que_limit=1):
        """
        :param app_eui: bytes
        :param device: Device
        :return:
        """
        # app_eui = hexlify(app_eui).decode()
        # if not db0.sismember(ConstDB.app_devs+app_eui, dev_eui):
        #     raise KeyError("Data enqueue failed. Device %s not registered in this app %s" % (hexlify(dev_eui).decode(), app_eui))
        # if isinstance(device, bytes):
        #     device = Device.query.get(device)
        # if app_eui is not None:
        hex_dev_eui = hexlify(dev_eui).decode()
        device_app_eui = db0.hget(ConstDB.dev + hex_dev_eui, FieldDevice.app_eui)
        if device_app_eui is None:
            raise KeyError("Data enqueue failed. Device %s is not active yet" % hex_dev_eui)
        if app_eui is not None:
            if device_app_eui != app_eui:
                raise KeyError("Data enqueue failed. Device %s not registered in this app %s" % (hex_dev_eui, hexlify(app_eui).decode()))
        self.dev_eui = dev_eui
        self.key = ConstDB.dev + hex_dev_eui
        self.que_limit = que_limit


    """
    settings
    bit |    7    |   6..5  |     4   | 3..0 |
        | cipher  |rx_window|confirmed|  rfu |
    """
    def push(self, fport, payload, cipher=True, seqno=None, confirmed=False, rx_window=0):
        assert isinstance(payload, bytes) and len(payload) < MAX_FRMPAYLOAD_LENGTH, 'Payload over Max Length'
        assert isinstance(fport, int) and 0 < fport < 255, 'FPort Error'
        assert isinstance(cipher, bool), 'Cipher Type Error'
        assert rx_window == 0 or rx_window == 1 or rx_window == 2, 'RX WINDOW ERROR'
        if self.que_limit <= self.len():
            raise QueOccupied('The queue of this Dev:%s is occupied' % hexlify(self.dev_eui).decode())
        fport = pack('B', fport)
        if cipher is False:
            appskey = db0.hget(self.key, FieldDevice.appskey)
            if len(appskey) != 16:
                raise AppSKeyAbsence(self.key)
            cipher = 0
        else:
            fcnt_down = int(db0.hget(self.key, FieldDevice.fcnt_down))
            que_len = self.len()
            seqno_expect = fcnt_down + que_len + 1
            if seqno != seqno_expect:
                raise SeqNoError(seqno, seqno_expect)
            cipher = 1
        settings = (cipher << 7) + (rx_window << 5) + (confirmed.real << 4)
        settings = bytes([settings])
        dev_class = ClassType(db0.hget(self.key, FieldDevice.dev_class).decode())
        if dev_class == ClassType.c and rx_window == 1:
            db0.rpush(ConstDB.que_down + self.key + ':1', settings + fport + payload)
        else:
            db0.rpush(ConstDB.que_down + self.key, settings + fport + payload)
        if dev_class == ClassType.c and (rx_window == 2 or rx_window == 0):
            db0.publish(Channel.que_down_alarm_c, self.key)
            Logger.info(action=Action.publish, resource=Resource.device, id=self.dev_eui, msg='Publish ' + Channel.que_down_alarm_c + ' ' + self.key)
        elif dev_class == ClassType.b:
            db0.publish(Channel.que_down_alarm_b, self.key)
            Logger.info(action=Action.publish, resource=Resource.device, id=self.dev_eui, msg='Publish ' + Channel.que_down_alarm_b + ' ' + self.key)


    def len(self):
        return db0.llen(ConstDB.que_down+self.key)

    def clear(self):
        return db0.delete(ConstDB.que_down+self.key)


QueDown.register(QueDownGroup)
QueDown.register(QueDownDev)