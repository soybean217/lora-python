from abc import ABCMeta, abstractmethod
from binascii import hexlify
from utils.db0 import ConstDB0, db0
from utils.exception import QueOccupied


class QueDown(metaclass=ABCMeta):
    @abstractmethod
    def pop(self):
        pass


class QueDownGroup(QueDown):
    def __init__(self, app_eui, id):
        """
        :param app_eui: bytes
        :param id: bytes
        :return:
        """
        app_eui = hexlify(app_eui).decode()
        key = ConstDB0.group + hexlify(id).decode()
        self.id = id
        if not db0.sismember(ConstDB0.app_groups+app_eui, id):
            raise KeyError("Data enqueue failed. Group %s not registered in this app %s" % (hexlify(id).decode(), app_eui))
        self.key = key

    def pop(self):
        return db0.lpop(ConstDB0.que_down + self.key)

    def len(self):
        return db0.llen(ConstDB0.que_down + self.key)

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, QueDownGroup), '%r is not a valid QueDownGroup' % value


class QueDownDev(QueDown):
    def __init__(self, dev_eui):
        """
        :param app_eui: bytes
        :param dev_eui: bytes
        :return:
        """
        # app_eui = hexlify(app_eui).decode()
        # if not db0.sismember(ConstDB0.app_devs+app_eui, dev_eui):
        #     raise KeyError("Data enqueue failed. Device %s not registered in this app %s" % (hexlify(dev_eui).decode(), app_eui))
        self.dev_eui = dev_eui
        self.key = ConstDB0.dev + hexlify(dev_eui).decode()

    def pop(self, class_c_rx1=None):
        if class_c_rx1 is None:
            return db0.lpop(ConstDB0.que_down + self.key)
        elif class_c_rx1 == 1:
            return db0.lpop(ConstDB0.que_down + self.key + ':1')

    def len(self):
        return db0.llen(ConstDB0.que_down+self.key)

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, QueDownDev), '%r is not a valid QueDownDev' % value


QueDown.register(QueDownGroup)
QueDown.register(QueDownDev)