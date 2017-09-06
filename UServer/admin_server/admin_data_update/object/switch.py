
class Assertions:

    @staticmethod
    def a_float(value):
        assert isinstance(value, float), 'Expect a float, but %r got' % value

    @staticmethod
    def a_int(value):
        assert isinstance(value, int), 'Expect a int, but %r got' % value

    @staticmethod
    def a_string(value):
        assert isinstance(value, str), 'Expect a str, but %r got' % value


class SwitchType:

    @staticmethod
    def float2string(value):
        Assertions.a_float(value)
        return '%.6f' % value

    @staticmethod
    def int2string(value):
        Assertions.a_int(value)
        return str(value)

    @staticmethod
    def string2float(value):
        Assertions.a_string(value)
        return float(value)

    @staticmethod
    def string2int(value):
        Assertions.a_string(value)
        return int(value)
