from database.db0 import db0, Channel, ConstDB
from utils.log import Logger, Resource, Action
from binascii import hexlify, unhexlify
from userver.object.device import ClassType
from userver.frequency_plan import frequency_plan


class ConstCMD:
    DutyCycleReq = b'\x04'
    RXParamSetupReq = b'\x05'
    DevStatusReq = b'\x06'
    NewChannelReq = b'\x07'
    RXTimingSetupReq = b'\x08'


class DevInfo:
    def __init__(self, device, MaxDutyCycle=0):
        self.device = device
        self.MaxDutyCycle = MaxDutyCycle


class MACCmd(object):
    def __init__(self, device, cid):
        """
        :param mac_cmd: bytes
        :param dev_eui: bytes
        :return:
        """
        self.device = device
        self.cid = cid

    def generate_payload(self):
        return b''

    def push_into_que(self):
        dev_eui = hexlify(self.device.dev_eui).decode()
        db0.set(ConstDB.mac_cmd + dev_eui + ':' + hexlify(self.cid).decode(), self.cid + self.generate_payload())
        que_key = ConstDB.mac_cmd_que + dev_eui
        db0.lrem(que_key, count=0, value=self.cid)
        db0.rpush(que_key, self.cid)
        if self.device.dev_class == ClassType.c:
            db0.publish(Channel.que_down_alarm_c, self.device.dev_eui)
            Logger.info(action=Action.publish, resource=Resource.device, id=dev_eui, msg='add_mac_cmd que_down_alarm_c:' + self.device.dev_eui)


class DevStatusReq(MACCmd):
    def __init__(self, device):
        super().__init__(device, ConstCMD.DevStatusReq)


class DutyCycleReq(MACCmd):
    def __init__(self, device, MaxDutyCycle):
        super().__init__(device, ConstCMD.DutyCycleReq)
        self.MaxDutyCycle = MaxDutyCycle

    def generate_payload(self):
        return bytes([self.MaxDutyCycle])


class RXParamSetupReq(MACCmd):
    def __init__(self, device, RX1DRoffset, RX2DataRate, frequency):
        """
        :param RX1DRoffset:
        :param RX2DataRate:
        :param frequency:
        :return:
        """
        FREQ_PLAN = frequency_plan[device.app.freq_plan]
        self.RX1DRoffset = RX1DRoffset if RX1DRoffset else FREQ_PLAN.RX1DRoffset
        self.RX2DataRate = RX2DataRate if RX2DataRate else FREQ_PLAN.RX2DataRate
        self.frequency = frequency if frequency else FREQ_PLAN.RX2Frequency
        assert isinstance(self.RX1DRoffset, int) and 0 <= self.RX1DRoffset <= 5, \
            'RX1DRoffset should be int and 0 <= delay <= 15. but got %s' % self.RX1DRoffset
        assert isinstance(self.RX2DataRate, int) and self.RX2DataRate in FREQ_PLAN.DataRateList, \
            'RX2DataRate should be int and in Range %s. but got %s' % (FREQ_PLAN.DataRateList, self.RX2DataRate)
        assert isinstance(self.frequency, float) and FREQ_PLAN.MinFrequency <= self.frequency <= FREQ_PLAN.MaxFrequency\
            , 'RX2Frequency should be float and in range of (%s, %s). but got %s' % (FREQ_PLAN.MinFrequency, FREQ_PLAN.MaxFrequency, self.frequency)
        super().__init__(device, ConstCMD.RXParamSetupReq)

    def generate_payload(self):
        dl_setting = bytes([self.RX2DataRate | (self.RX1DRoffset << 4)])
        frequency = (int(self.frequency * 1000)).to_bytes(3, 'little')
        return dl_setting + frequency


class RXTimingSetupReq(MACCmd):
    def __init__(self, device, delay):
        """
        :param device:
        :param delay:
        :return:
        """
        assert isinstance(delay, int) and 0 <= delay <= 15, 'delay should be int and 0 <= delay <= 15. but got %s' % delay
        self.delay = delay
        super().__init__(device, ConstCMD.RXTimingSetupReq)

    def generate_payload(self):
        return bytes([self.delay])


