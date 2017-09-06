from frequency_plan import Frequency
from enum import Enum


class CN470_510(Frequency):
    JOIN_ACCEPT_DELAY = 5
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

    RX2Frequency = 505.3
    RX2DataRate = 0
    RX1DRoffset = 0
    RxDelay = 1

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

    @classmethod
    def rx1_datr(cls, dr_up, dr_offset):
        """
        :param dr_up: int
        :param dr_offset: int
        :return: DataRate
        """
        assert 0 <= dr_up <= 5
        assert 0 <= dr_offset <= 3
        dr_dn = dr_up - dr_offset
        if dr_dn < 0:
            dr_dn = 0
        return cls.DataRate(dr_dn)

    @classmethod
    def rx1_freq(cls, freq_up):
        """
        :param freq_up: float (MHz)
        :return: float (MHz)
        """
        chan_up = cls.get_channel_up_by_freq(freq_up)
        chan_dn = chan_up % 48
        freq_dn = cls.get_freq_dn_by_channel(chan_dn)
        return freq_dn

    @staticmethod
    def get_freq_dn_by_channel(channel):
        """
        :param channel: int
        :return: float (MHz)
        """
        assert 0 <= channel <= 47
        # print(channel)
        # print(500.3 + 0.2 * channel)
        return 500 + (3 + 2 * channel)/10
        # return 500.3 + 0.2 * channel

    @staticmethod
    def get_channel_up_by_freq(frequency):
        """
        :param frequency: float (MHz)
        :return:
        """
        assert 470.3 <= frequency <= 489.3, 'CN470_510 Frequency Plan got Frequency: %s'%frequency
        channel = (frequency - 470.3) / 0.2
        decimal = channel % 1
        if decimal >= 0.5:
            channel = int(channel) + 1
        else:
            channel = int(channel)
        return int(channel)

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

    MAX_LENGTH = {
        DataRate.SF12BW125: 59,
        DataRate.SF11BW125: 59,
        DataRate.SF10BW125: 59,
        DataRate.SF9BW125: 123,
        DataRate.SF8BW125: 230,
        DataRate.SF7BW125: 230,
    }

    @staticmethod
    def adr_schema(rssi, recent_datr):
        if -57 < rssi:
            return 5
        elif -60 < rssi <= -57:
            if recent_datr == 4:
                return recent_datr
            else:
                return 5
        elif -67 < rssi <= -60:
            return 4
        elif -70 < rssi <= -67:
            if recent_datr == 3:
                return recent_datr
            else:
                return 4
        elif -77 < rssi <= -70:
            return 3
        elif -80 < rssi <= -77:
            if recent_datr == 2:
                return recent_datr
            else:
                return 3
        elif -87 < rssi <= -80:
            return 2
        elif -90 < rssi <= -87:
            if recent_datr == 1:
                return recent_datr
            else:
                return 2
        elif -107 < rssi <= -90:
            return 1
        elif -100 < rssi <= -107:
            if recent_datr == 0:
                return recent_datr
            else:
                return 1
        else:
            return 0
        # else:
        #     logger.error(ConstLog.adr + 'rssi %s recent_datr %s' % (rssi, recent_datr))

if __name__ == '__main__':
    print(CN470_510.rx1_freq(470.9))