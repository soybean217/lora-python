from utils.db0 import db0, ConstDB
from utils.log import logger, ConstLog
from utils.errors import ReadOnlyDeny
from binascii import hexlify
from enum import Enum
from object.asserts import Assertions
from .frequency_plan import FrequencyPlan


class Platform(Enum):
    RaspBerryPi = 'rpi'
    LinkLabs = 'linklabs'
    RaspBerryPi3 = 'rpi3'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Platform), '%r is not a valid Platform' % value


class Model(Enum):
    IMST = 'imst'
    LinkLabs = 'linklabs'
    MenThink = 'menthink'
    RisingHF = 'risinghf'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Model), '%r is not a valid Model' % value


# class Model:
#     class RaspBerryPi(Enum):
#         RaspBerryPi2 = "rpi_2"
#         RaspBerryPiB = "rpi_b"
#
#         def __str__(self):
#             return {'RaspBerryPi2': 'RaspBerryPi 2', 'RaspBerryPiB': 'RaspBerryPi B/B+'}[self._name_]
#
#         @staticmethod
#         def assert_isinstanceof(value):
#             assert isinstance(value, Model.RaspBerryPi), '%r is not a valid Model' % value



class Field:
    id = 'id'
    name = 'name'
    platform = 'platform'
    model = 'model'
    concentrator = 'concentrator'
    frequency = 'frequency'
    freq_plan = 'freq_plan'
    public = 'public'
    disable = 'disable'
    time = 'time'
    lng = 'lng'
    lat = 'lat'
    alt = 'alt'
    location = 'location'
    user_id = 'user_id'
    sys_ver = 'sys_ver'


class Location:
    _assert_switcher = {Field.lng: Assertions.a_float,
                        Field.lat: Assertions.a_float,
                        Field.alt: Assertions.a_int, }

    def __setattr__(self, key, value):
        self._assert_switcher[key](value)
        self.__dict__[key] = value

    def __init__(self, lng, lat, alt):
        self.lng = lng
        self.lat = lat
        self.alt = alt

    def __str__(self):
        return '%.4f,%.4f,%i' % (self.lng, self.lat, self.alt)

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, Location), '%r is not a valid Location' % value

    class objects:
        @staticmethod
        def str_to_obj(string):
            string = string.split(',')
            try:
                return Location(float(string[0]), float(string[1]), int(string[2]))
            except Exception as error:
                raise error


class Gateway(object):
    _assert_switcher = {
                        Field.id: Assertions.a_eui,
                        Field.name: Assertions.a_str,
                        Field.platform: Platform.assert_isinstanceof,
                        Field.model: Model.assert_isinstanceof,
                        Field.freq_plan: FrequencyPlan.assert_isinstanceof,
                        Field.location: Location.assert_isinstanceof,
                        }

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise ReadOnlyDeny
        assert_method = self._assert_switcher.get(key)
        if assert_method is not None:
            self._assert_switcher[key](value)
        self.__dict__[key] = value

    def __init__(self, id, platform, model, freq_plan, location=None):
        """
        :param id: 8 bytes
        :param name: str
        :param platform: Platform
        :return:
        """
        self.id = id
        self.platform = platform
        self.model = model
        self.freq_plan = freq_plan
        if location is not None:
            self.location = location
        else:
            self.location = Location(0.0, 0.0, 0)

    class objects:
        @staticmethod
        def get(id):
            """
            :param id: 8 bytes
            :return:
            """
            try:
                info = db0.hgetall(ConstDB.gateway + hexlify(id).decode())
                freq_plan = FrequencyPlan(info[b'freq_plan'].decode())
                platform = Platform(info[b'platform'].decode())
                model = Model(info[b'model'].decode())
                location = info.get(b'location')
                if location is not None:
                    location = Location.objects.str_to_obj(location.decode())
                gateway = Gateway(id, platform, model, freq_plan, location)
                return gateway
            except Exception as error:
                raise
                logger.error(ConstLog.gateway + '%r' % error)