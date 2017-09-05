class Assertions:
    @staticmethod
    def a_eui(eui):
        assert isinstance(eui, bytes) and len(eui) == 8

    @staticmethod
    def a_str(value):
        assert isinstance(value, str)

    @staticmethod
    def a_bool(value):
        assert isinstance(value, bool)

    @staticmethod
    def a_int(value):
        assert isinstance(value, int)

    @staticmethod
    def a_float(value):
        assert isinstance(value, float)