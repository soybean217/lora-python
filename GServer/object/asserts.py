from object.fields import ClassType


class Assertions:
    @staticmethod
    def a_eui(eui):
        assert isinstance(eui, bytes) and len(eui) == 8

    @staticmethod
    def a_addr(addr):
        assert isinstance(addr, bytes) and len(addr) == 4

    @staticmethod
    def a_nwkskey(nwkskey):
        assert isinstance(nwkskey, bytes) and len(nwkskey) == 16

    @staticmethod
    def a_appskey(appskey):
        assert isinstance(appskey, bytes) and (len(appskey) == 16 or len(appskey) == 0)

    @staticmethod
    def a_fcnt(fcnt):
        assert isinstance(fcnt, int) and 0 <= fcnt < 0x100000000

    @staticmethod
    def a_dev_class(dev_class):
        assert isinstance(dev_class, ClassType)

    @staticmethod
    def a_rx_window(rx_window):
        assert rx_window == 1 or rx_window == 2

    @staticmethod
    def a_periodicity(periodicity):
        assert isinstance(periodicity, int) and 0 <= periodicity <=7

    @staticmethod
    def a_group_dev_eui(eui):
        assert isinstance(eui, str)
        eui_split = eui.split(':')
        if eui_split[0] == 'GROUP':
            assert len(eui_split) == 2, 'eui is not valid: %s' % eui
        elif eui_split[0] == 'DEV':
            assert len(eui_split) == 2, 'eui is not valid: %s' % eui
        else:
            raise AssertionError('eui is not valid: %s' % eui)

    @staticmethod
    def a_positive_int(value):
        assert isinstance(value, int) and value > 0, '%r is not a positive int' % value

    @staticmethod
    def a_positive_num(value):
        assert isinstance(value, (int, float)) and value > 0, '%r is not a positive number' % value

    @staticmethod
    def a_not_negative_int(value):
        assert isinstance(value, int) and value >= 0

    @staticmethod
    def a_float(value):
        assert isinstance(value, float)

    @staticmethod
    def a_int(value):
        assert isinstance(value, int)

    @staticmethod
    def a_str(value):
        assert isinstance(value, str)

    @staticmethod
    def a_bool(value):
        assert isinstance(value, bool)

    @staticmethod
    def a_bytes(value):
        assert isinstance(value, bytes)

    @staticmethod
    def a_list(value):
        assert isinstance(value, list)

    @staticmethod
    def a_pass(value):
        pass