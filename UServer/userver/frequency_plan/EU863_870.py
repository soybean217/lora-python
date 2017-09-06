from . import Frequency
from enum import Enum


class EU863_870(Frequency):
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
        SF7BW250 = 6
        FSK = 7

    # ------------------------------------
    DataRateList = (0, 1, 2, 3, 4, 5)

    RxDelay = 1

    RX2DataRate = 0
    RX1DRoffset = 0
    RX2Frequency = 869.525

    MinFrequency = 863.0
    MaxFrequency = 870.0
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

    BEACON_FREQ = 869.525

    class Channel:
        """
        Default Freq Ch1 868.1
        Default Freq Ch2 868.3
        Default Freq Ch3 868.5
        Ch4 Freq 867.1 * (10 ** 4) 8671000
        Ch5 Freq 867.3 8673000
        Ch6 Freq 867.5 8675000
        Ch7 Freq 867.7 8677000
        Ch8 Freq 867.9 8679000
        Ch9 lora-std Freq 868.3 SF7BW250
        """
        Ch4 = 8671000
        Ch5 = 8673000
        Ch6 = 8675000
        Ch7 = 8677000
        Ch8 = 8679000
        CF_LIST = Ch4.to_bytes(3, 'little') + Ch5.to_bytes(3, 'little') + \
                  Ch6.to_bytes(3, 'little') + Ch7.to_bytes(3, 'little') + \
                  Ch8.to_bytes(3, 'little') + bytes([0])
        CH_MASK = b'\xff\x01'     # Ch1-9 open
        CH_MASK_CNTL = 0
        NB_TRANS = 1

    class TXPower(Enum):
        dBm20 = 0
        dBm14 = 1
        dBm11 = 2
        dBm8 = 3
        dBm5 = 4
        dBm2 = 5
        default = 1

    MAX_LENGTH = {
        DataRate.SF12BW125: 51,
        DataRate.SF11BW125: 51,
        DataRate.SF10BW125: 51,
        DataRate.SF9BW125: 115,
        DataRate.SF8BW125: 222,
        DataRate.SF7BW125: 222,
        DataRate.SF7BW250: 222,
        DataRate.FSK: 222,
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