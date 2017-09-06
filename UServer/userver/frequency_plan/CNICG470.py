from . import Frequency
from enum import Enum


class CNICG470(Frequency):
    RECEIVE_DELAY1 = 1
    RECEIVE_DELAY2 = 2
    JOIN_ACCEPT_DELAY1 = 5
    JOIN_ACCEPT_DELAY2 = 6
    MAX_FCNT_GAP = 16384
    ADR_ACK_LIMIT = 64
    ADR_ACK_DELAY = 32
    ACK_TIMEOUT = 2    # 2 +/-1 s random delay between 1 and 3 seconds

    RF_CH = 0

    class DataRate(Enum):
        SF12BW125 = 0
        SF11BW125 = 1
        SF10BW125 = 2
        SF9BW125 = 3
        SF8BW125 = 4
        SF7BW125 = 5

    # ------------------------------------
    DataRateList = (0, 1, 2, 3, 4, 5)

    RxDelay = 1

    RX2DataRate = 0
    RX1DRoffset = 0
    RX2Frequency = 470.3

    MinFrequency = 470.0
    MaxFrequency = 510.0
    # ------------------------------------

    RX2_FREQ = 869.525
    RX2_DR = DataRate(0)

    @classmethod
    def rx1_freq(cls, freq_up):
        return freq_up

    @classmethod
    def rx1_datr(cls, dr_up, dr_offset):
        """
        :param dr_up: int
        :param dr_offset: int
        :return: str like "SF7BW250"
        """
        assert 0 <= dr_up <= 7
        assert 0 <= dr_offset <= 5
        dr_dn = dr_up - dr_offset
        if dr_dn < 0:
            dr_dn = 0
        return cls.DataRate(dr_dn)

    @classmethod
    def b_freq(cls):
        return cls.BEACON_FREQ

    BEACON_FREQ = 470.3

    class Channel:
        """
        Ch1 470.3
        Ch2 470.5
        Ch3 470.7
        Ch4 470.9
        Ch5 471.1
        Ch6 471.3
        Ch7 471.5
        Ch8 471.7
        """
        CF_LIST = b''
        CH_MASK = b'\xff\x00'     # Ch1-8 open
        CH_MASK_CNTL = 0
        NB_TRANS = 1

    class TXPower(Enum):
        dBm17 = 0
        dBm16 = 1
        dBm14 = 2
        dBm12 = 3
        dBm10 = 4
        dBm7 = 5
        dBm5 = 6
        dBm2 = 7
        default = 7

    MAX_LENGTH = {
        DataRate.SF12BW125: 51,
        DataRate.SF11BW125: 51,
        DataRate.SF10BW125: 51,
        DataRate.SF9BW125: 115,
        DataRate.SF8BW125: 222,
        DataRate.SF7BW125: 222,
    }

    # @staticmethod
    # def adr_schema(rssi, recent_datr):
    #     if rssi > -47:
    #         return 6
    #     elif -50 < rssi <= -47:
    #         if recent_datr == 5:
    #             return recent_datr
    #         else:
    #             return 6
    #     elif -57 < rssi <= -50:
    #         return 5
    #     elif -60 < rssi <= -57:
    #         if recent_datr == 4:
    #             return recent_datr
    #         else:
    #             return 5
    #     elif -67 < rssi <= -60:
    #         return 4
    #     elif -70 < rssi <= -67:
    #         if recent_datr == 3:
    #             return recent_datr
    #         else:
    #             return 4
    #     elif -77 < rssi <= -70:
    #         return 3
    #     elif -80 < rssi <= -77:
    #         if recent_datr == 2:
    #             return recent_datr
    #         else:
    #             return 3
    #     elif -87 < rssi <= -80:
    #         return 2
    #     elif -90 < rssi <= -87:
    #         if recent_datr == 1:
    #             return recent_datr
    #         else:
    #             return 2
    #     elif -107 < rssi <= -90:
    #         return 1
    #     elif -110 < rssi <= -107:
    #         if recent_datr == 0:
    #             return recent_datr
    #         else:
    #             return 1
    #     elif rssi <= -110:
    #         return 0
    #     else:
    #         logger.error(ConstLog.adr + 'rssi %s recent_datr %s' % (rssi, recent_datr))

"""
rssi range from Rossi:
        'SF12BW125': -110~,
        'SF11BW125': -90~-110,
        'SF10BW125': -80~-90,
        'SF9BW125': -70~-80,
        'SF8BW125': -60~-70,
        'SF7BW125': -50~60,
        'SF7BW250': 0~-50,
        'FSK': ,
"""