from enum import Enum
from utils.db0 import db0, ConstDB0, Channel0
from binascii import hexlify
from object.device import FieldDevice, DeviceACK, ACKName, Device, DevInfo
from object.fields import ClassType, FieldDevice
# from utils.log import logger, ConstLog
from utils.log import Logger, Action, IDType

class CID:
    LinkCheckReq = b'\x02'
    LinkCheckAns = b'\x02'
    LinkADRReq = b'\x03'
    LinkADRAns = b'\x03'
    DutyCycleReq = b'\x04'
    DutyCycleAns = b'\x04'
    RXParamSetupReq = b'\x05'
    RXParamSetupAns = b'\x05'
    DevStatusReq = b'\x06'
    DevStatusAns = b'\x06'
    NewChannelReq = b'\x07'
    NewChannelAns = b'\x07'
    RXTimingSetupReq = b'\x08'
    RXTimingSetupAns = b'\x08'
    PingSlotInfoReq = b'\x10'
    PingSlotInfoAns = b'\x10'
    PingSlotChannelReq = b'\x11'
    PingSlotFreqAns = b'\x11'
    BeaconTimingReq = b'\x12'
    BeaconTimingAns = b'\x12'
    BeaconFreqReq = b'\x13'
    BeaconFreqAns = b'\x13'

   # Proprietary  = 0x80~0xff


class MACCmd(object):

    def __init__(self, dev_eui):
        """
        :param dev_eui: bytes
        :return:
        """
        device = Device.objects.get(dev_eui)
        if device is not None:
            self.device = device
        else:
            raise KeyError('Device %s Not Found' % hexlify(dev_eui).decode())

    @staticmethod
    def __return_data(cid, payload):
        """
        :return: bytes
        """
        if payload is not None:
            cmd = cid + payload
        else:
            cmd = cid
        return cmd
    
    def push_into_que(self, cid, payload=None):
        dev_eui = hexlify(self.device.dev_eui).decode()
        db0.set(ConstDB0.mac_cmd + dev_eui + ':' + hexlify(cid).decode(), self.__return_data(cid, payload))
        que_key = ConstDB0.mac_cmd_que + dev_eui
        db0.lrem(que_key, count=0, value=cid)
        db0.rpush(que_key, cid)
        dev_class = ClassType(db0.hget(ConstDB0.dev + dev_eui, FieldDevice.dev_class).decode())
        if dev_class == ClassType.c or dev_class == ClassType.b:
            db0.publish(Channel0.que_down_alarm_c, ConstDB0.dev + dev_eui)
            # logger.info(ConstLog.publish + 'add_mac_cmd que_down_alarm_c:' + ConstDB0.dev + dev_eui)

    def pop_from_que(self, max_len):
        dev_eui = hexlify(self.device.dev_eui).decode()
        mac_cmd = b''
        while db0.exists(ConstDB0.mac_cmd_que + dev_eui):
            cid = db0.lpop(ConstDB0.mac_cmd_que + dev_eui)
            if cid is not None:
                cmd = db0.get(ConstDB0.mac_cmd + dev_eui + ':' + hexlify(cid).decode())
                if cmd is not None:
                    total_len = len(mac_cmd) + len(cmd)
                    if total_len < 15 and total_len < max_len:
                        mac_cmd += cmd
                        update_device_info(self.device.dev_eui, cid, cmd)
                    else:
                        db0.lpush(ConstDB0.mac_cmd_que + dev_eui, cid)
                        break
        return mac_cmd


def update_device_info(dev_eui, cid, cmd):
    if cid == CID.DutyCycleReq:
        MaxDutyCycle = cmd[1]
        DevInfo(dev_eui).set_p_value(MaxDutyCycle=MaxDutyCycle)
    elif cid == CID.RXParamSetupReq:
        RX1DRoffset = cmd[1] & 0b00001111
        RX2DataRate = cmd[1] >> 4
        RX2Frequency = int.from_bytes(cmd[2:], 'little') / 1000.0
        DevInfo(dev_eui).set_p_value(RX1DRoffset=RX1DRoffset, RX2DataRate=RX2DataRate, RX2Frequency=RX2Frequency)
    elif cid == CID.RXTimingSetupReq:
        RxDelay = cmd[1]
        DevInfo(dev_eui).set_p_value(RxDelay=RxDelay)


class LinkCheckAnsPayload:
    def __init__(self, margin, gw_cnt):
        """
        :param Margin: bytes len(Margin) = 1
        :param GwCnt: bytes  len(GwCnt) = 1
        :return:bytes
        """
        assert isinstance(margin, bytes) and len(margin) == 1, 'WRONG mannrgin'
        assert isinstance(gw_cnt, bytes) and len(gw_cnt) == 1, 'WRONG gw_cnt'
        self.margin = margin
        self.gw_cnt = gw_cnt

    def return_data(self):
        return self.margin + self.gw_cnt


class LinkADRReqPayload:
    def __init__(self, data_rate, tx_power, ch_mask, ch_mask_cntl, nb_trans):
        self.data_rate = data_rate
        self.tx_power = tx_power
        self.ch_mask = ch_mask
        self.ch_mask_cntl = ch_mask_cntl
        self.nb_trans = nb_trans

    def return_data(self):
        """
        :return: bytes
        """
        DataRate_TXPower = bytes([self.tx_power | (self.data_rate << 4)])
        Redundancy = bytes([self.nb_trans | (self.ch_mask_cntl << 4) | (0 << 7)])
        link_adr_req_payload = DataRate_TXPower + self.ch_mask + Redundancy
        return link_adr_req_payload


class DutyCycleReqPayload:
    def __init__(self, max_duty_cycle):
        ''' 
        :param max_duty_cycle: bytes len(max_duty_cycle) = 1
        :return: bytes
        '''
        assert isinstance(max_duty_cycle, bytes) and len(max_duty_cycle) == 1, 'WRONG MaxDutyCycle'
        self.max_duty_cycle = max_duty_cycle

    def return_data(self):
        return self.max_duty_cycle


class RXParamSetupReq:
    def __init__(self, RX1DRoffset, RX2DataRate, frequency, rfu=0):
        """
        :param RX1DRoffset:
        :param RX2DataRate:
        :param frequency:
        :return:
        """
        self.RX1DRoffset = RX1DRoffset
        self.RX2DataRate = RX2DataRate
        self.frequency = frequency
        self.rfu = rfu

    def return_data(self):
        dl_setting = bytes([self.RX2DataRate | (self.RX1DRoffset << 4) | (self.rfu << 1)])
        return dl_setting + self.frequency


class NewChannelReq:
    def __init__(self, ch_index, freq, max_dr, min_dr):
        """
        :param ch_index: 1 bytes
        :param freq: 3 bytes
        :param max_dr: int
        :param min_dr: int
        :return:
        """
        self.ch_index = ch_index
        self.freq = freq
        self.max_dr = max_dr
        self.min_dr = min_dr

    def return_data(self):
        dr_range = bytes([self.max_dr << 4 | self.min_dr])
        return self.ch_index + self.freq + dr_range


class RXTimingSetupReq:
    def __int__(self, delay, rfu=0):
        '''
        :param delay: int 0~15
        :return:
        '''
        assert isinstance(delay, int) and delay in range(0, 16), 'WRONG delay value or type,must be int and in range(0,16)'
        assert isinstance(rfu, int) and rfu in range(0, 16), 'WRONG rfu value or type,must be int and in range(0,16)'
        self.delay = delay
        self.rfu = rfu

    def return_data(self):
        return bytes([self.rfu << 4 | self.delay])


class PingSlotChannelReq:
    def __init__(self, freq, max_dr, min_dr):
        assert type(freq) is int, "WRONG freq format"
        # freq in Hz
        assert freq in range(1000000, 16700000), "freq out of range ,should in range(1M,16.7M)"
        assert type(min_dr) is int, "WRONG min_dir format"
        assert type(max_dr) is int, "WRONG max_dir format"
        self.freq = freq
        self.max_dr = max_dr
        self.min_dr = min_dr

    def return_data(self):
        dr_range = bytes([self.max_dr << 4 | self.min_dr])
        return int.to_bytes(self.freq, 3, 'little') + dr_range


class BeaconFreqReq:
    def __init__(self, freq):
        assert type(freq) is int, "WRONG freq format"
        assert freq in range(1000000, 16700000), "freq out of range ,should in range(1M,16.7M)"
        self.freq = freq

    def return_data(self):
        return int.to_bytes(self.freq, 3, 'little')


class BeaconTimingAns:
    def __init__(self, delay, channel):
        assert type(delay) is int, "WRONG dalay format"
        assert type(channel) is int, "WRONG channel format"
        self.delay = delay
        self.channel = channel

    def return_data(self):
        return int.to_bytes(self.delay, 2, 'little') + int.to_bytes(self.channel, 1, "little")


class DlChannelReq:
    def __init__(self, index, freq):
        """
        :param index:
        :param freq: Hz
        :return:
        """
        self.index = index
        self.freq = freq

    def return_data(self):
        freq = int(self.freq / 100).to_bytes(length=3, byteorder='big')
        index = int(self.index).to_bytes(length=1, byteorder='big')
        return index + freq

# if __name__ == '__main__':
#     print("go")
#     # payload = link_adr_req_payload(b'\x03',b'\x03',b'\x03\x03',b'\x01',b'\x03',b'\x03').return_data()
#     payload = link_adr_req_payload(3).return_data()
#
#     # cmd1 = trying(1,2,3)
#     cmd1 = mac_cmd(_cid.LinkADRReq,payload=payload).return_data()
#     print(cmd1,len(cmd1),type(cmd1))
#
#     mcp = redis_db
#     mcp.put('aaaaaaaabbbbbbb4',cmd1)
#     print(mcp.empty('aaaaaaaabbbbbbb4'))
#     # c = mcp.get('aaaaaaaabbbbbbb4')
#     # print(c)
#     print("finished")