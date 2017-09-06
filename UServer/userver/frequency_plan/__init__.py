from abc import ABC, abstractmethod, abstractproperty, abstractclassmethod, abstractstaticmethod
from enum import Enum


class FrequencyPlan(Enum):
    EU863_870 = 'EU863_870'
    EU433 = 'EU433'
    CN470_510 = 'CN470_510'
    MT433 = 'MT433'
    CP500 = 'CP500'
    CNICG470 = 'CNICG470'

    @staticmethod
    def assert_isinstanceof(value):
        assert isinstance(value, FrequencyPlan), '%r is not a valid Frequency' % value


class Frequency(ABC):
    @abstractclassmethod
    def rx1_freq(cls, freq_up):
        pass

    @abstractclassmethod
    def rx1_datr(cls, dr_up, dr_offset):
        pass

    @abstractproperty
    class DataRate(Enum):
        pass

    @abstractproperty
    class Channel:
        pass

    @abstractproperty
    class TXPower(Enum):
        pass

    # @abstractstaticmethod
    # def adr_schema(rssi, recent_datr):
    #     pass

    @staticmethod
    def get_freq_plan(freq_plan):
        return frequency_plan[freq_plan]

from .CN470_510 import CN470_510
from .EU863_870 import EU863_870
from .EU433 import EU433
from .MT433 import MT433
from .CP500 import CP500
from .CNICG470 import CNICG470

Frequency.register(CN470_510)
Frequency.register(EU863_870)
Frequency.register(EU433)
Frequency.register(MT433)
Frequency.register(CP500)
Frequency.register(CNICG470)


frequency_plan = {
    FrequencyPlan.EU863_870: EU863_870,
    FrequencyPlan.EU433: EU433,
    FrequencyPlan.CN470_510: CN470_510,
    FrequencyPlan.MT433: MT433,
    FrequencyPlan.CP500: CP500,
    FrequencyPlan.CNICG470: CNICG470
}