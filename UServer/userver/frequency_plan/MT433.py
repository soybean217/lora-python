from . import Frequency
from enum import Enum


class MT433(Frequency):
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
    RX2Frequency = 434.665

    MinFrequency = 433.175
    MaxFrequency = 434.665
    # ------------------------------------

    RX2_FREQ = 434.665
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

    class Channel:
        """
        Default Ch1 Freq 433.3
        Default Ch2 Freq  433.5
        Default Ch3 Freq  433.7
        Ch4 Freq 433.9 * (10 ** 4) 4339000
        Ch5 Freq 434.0 4340000
        Ch6 Freq 434.2 4342000
        Ch7 Freq 434.4 4342000
        Ch8 Freq 434.6 4342000
        """
        Ch4 = 4339000
        Ch5 = 4340000
        Ch6 = 4342000
        Ch7 = 4344000
        Ch8 = 4346000
        CF_LIST = Ch4.to_bytes(3, 'little') + Ch5.to_bytes(3, 'little') + \
                  Ch6.to_bytes(3, 'little') + Ch7.to_bytes(3, 'little') + \
                  Ch8.to_bytes(3, 'little') + bytes([0])
        CH_MASK = b'\xff\x00'     # Ch1-8 open
        CH_MASK_CNTL = 0
        NB_TRANS = 1

    class TXPower(Enum):
        dBm10 = 0
        dBm7 = 1
        dBm4 = 2
        dBm1 = 3
        dBmN2 = 4
        dBmN5 = 5
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