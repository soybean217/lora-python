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