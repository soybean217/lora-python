from . import Frequency
from enum import Enum


class CP500(Frequency):
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
    DataRateList = (0, 1, 2, 3, 4, 5, 6, 7)

    RxDelay = 1

    RX2DataRate = 0
    RX1DRoffset = 0
    RX2Frequency = 501.7

    MinFrequency = 470.0
    MaxFrequency = 510.0
    # ------------------------------------

    RX2_FREQ = 501.7
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

    BEACON_FREQ = 501.7

    class Channel:
        """
        Default Freq Ch1 500.3
        Default Freq Ch2 500.5
        Default Freq Ch3 500.7
        Ch4 Freq 500.9 * (10 ** 4) 8671000
        Ch5 Freq 501.1 8673000
        Ch6 Freq 501.3 8675000
        Ch7 Freq 501.5 8677000
        Ch8 Freq 501.7 8679000
        Ch9 lora-std Freq 868.3 SF7BW250
        """
        Ch4 = 5009000
        Ch5 = 5011000
        Ch6 = 5013000
        Ch7 = 5015000
        Ch8 = 5017000
        CF_LIST = Ch4.to_bytes(3, 'little') + Ch5.to_bytes(3, 'little') + \
                  Ch6.to_bytes(3, 'little') + Ch7.to_bytes(3, 'little') + \
                  Ch8.to_bytes(3, 'little') + bytes([0])
        CH_MASK = b'\xff\x00'     # Ch1-8 open
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