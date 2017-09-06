from .const import ClassType
from datetime import datetime


class Assertions:

    @staticmethod
    def a_eui_64(eui):
        assert isinstance(eui, bytes) and len(eui) == 8, 'Expect 8 bytes but got %s' % eui

    @staticmethod
    def a_eui_48(eui):
        assert isinstance(eui, bytes) and len(eui) == 6, 'Expect 6 bytes but got %s' % eui

    @staticmethod
    def a_token(token):
        assert isinstance(token, bytes) and len(token) == 16, 'Expect 16 bytes but got %s' % token

    @staticmethod
    def a_dev_addr(dev_addr):
        assert isinstance(dev_addr, bytes) and len(dev_addr) == 4, 'Expect 4 bytes but got %s' % dev_addr

    @staticmethod
    def a_nwkskey(nwkskey):
        assert isinstance(nwkskey, bytes) and len(nwkskey) == 16, 'Expect 16 bytes but got %s' % nwkskey

    @staticmethod
    def a_appskey(appskey):
        assert isinstance(appskey, bytes) and (len(appskey) == 16 or len(appskey) == 0), 'Expect 0 or 16 bytes but got %s' % appskey

    @staticmethod
    def a_fcnt(fcnt):
        assert isinstance(fcnt, int) and 0 <= fcnt < 0x100000000, 'Fcnt expect int in range (0,4294967296) but got %s' % type(fcnt)

    @staticmethod
    def a_dev_class(dev_class):
        assert isinstance(dev_class, ClassType), '%r is not a vail device class' % dev_class

    @staticmethod
    def a_rx_window(rx_window):
        assert rx_window == 1 or rx_window == 2, '%r is not a vail rx window, Except 1 or 2' % rx_window

    @staticmethod
    def a_group_dev_eui(eui):
        assert isinstance(eui, str)
        eui_split = eui.split(':')
        if eui_split[0] == 'GROUP':
            assert len(eui) == 3
        elif eui_split[0] == 'DEV':
            assert len(eui) == 2
        else:
            raise AssertionError('eui is not valid: %s' % eui)

    @staticmethod
    def a_periodicity(periodicity):
        assert isinstance(periodicity, int), 'periodicity should be int but got %s' % periodicity
        if not 0 <= periodicity <= 7:
            raise AssertionError('periodicity %s is out or range [0,7]' % periodicity)

    @staticmethod
    def a_datarate(datarate):
        assert isinstance(datarate, int), 'datarate should be int but got %s' % datarate
        if not 0 <= datarate <= 7:
            raise AssertionError('datarate %s is out or range [0,7]' % datarate)

    @staticmethod
    def a_bytes(value):
        assert isinstance(value, bytes), 'Expect a bytes, but %r got' % value

    @staticmethod
    def a_positive_int(value):
        assert isinstance(value, int) and value > 0, 'Expect a positive int, but %r got' % value

    @staticmethod
    def a_int(value):
        assert isinstance(value, int), 'Expect a int, but %r got' % value

    @staticmethod
    def a_not_negative_int(value):
        assert isinstance(value, int) and value >= 0, 'Expect a negative int, but %r got' % value

    @staticmethod
    def a_str(value):
        assert isinstance(value, str), 'Expect a str but %r got' % value

    @staticmethod
    def a_bool(value):
        assert isinstance(value, bool), 'Expect a boolean(True or False), but %r got' % value

    @staticmethod
    def a_float(value):
        assert isinstance(value, float), 'Expect a float, but %r got' % value

    @staticmethod
    def a_datetime(value):
        assert isinstance(value, datetime), 'Expect a datetime, but %r got' % value

    @staticmethod
    def a_pass(value):
        pass

    @staticmethod
    def s_addr(addr):
        assert isinstance(addr, str) and len(addr) == 8, '%s is not a vail addr, Except 8 hex digits' % addr

    @staticmethod
    def s_nwkskey(nwkskey):
        assert isinstance(nwkskey, str) and len(nwkskey) == 32, '%s is not a vail NWKSKEY, Except 32 hex digits' % nwkskey

    @staticmethod
    def s_appskey(appskey):
        assert isinstance(appskey, str) and (len(appskey) == 32 or len(appskey) == 0), '%s is not a vail APPSKEY, Except 32 or 0 hex digits' % appskey

    @staticmethod
    def s_appkey(appkey):
        assert appkey is None or (isinstance(appkey, str) and len(appkey) == 32), '%s is not a vail APPKEY, Except 32 hex digits' % appkey

    @staticmethod
    def a_appkey(appkey):
        assert isinstance(appkey, bytes) and len(appkey) == 16, 'Appkey expect 16 bytes but got %s' % appkey
