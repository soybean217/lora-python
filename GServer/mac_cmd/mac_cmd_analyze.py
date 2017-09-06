import time
import ctypes
from binascii import hexlify
from object.class_b import ClassBInfo, BeaconTiming
from object.device import DevInfo
from utils.db0 import db0, ConstDB0
from utils.log import Logger, IDType, Action
from mac_cmd.const import MACConst
from mac_cmd.mac_cmd_gen import CID, LinkCheckAnsPayload, MACCmd, BeaconTimingAns


def analyze_LinkCheckReq(device, cmd_payload):
    assert len(cmd_payload) == 0, 'WRONG MAC CMD PAYLOAD OF LinkCheckReq'
    Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg='LinkCheckReq: %s' % cmd_payload)
    cnt = db0.zcard(ConstDB0.dev_gateways+hexlify(device.dev_eui).decode())
    #gen a ans down
    margin = b'\x00'
    GwCnt = bytes([cnt])
    payload = LinkCheckAnsPayload(margin, GwCnt).return_data()
    mac_cmd = MACCmd(device.dev_eui)
    #push into que
    mac_cmd.push_into_que(CID.LinkCheckAns, payload)


# @debuger('analyze_LinkADRAns')
# @timeStumpFunc('analyze_LinkADRAns')
def analyze_LinkADRAns(device, cmd_payload):
    assert len(cmd_payload) == 1, 'WRONG MAC CMD PAYLOAD OF LinkADRAns'
    cmd_payload = cmd_payload[0]
    channel_mask_ack = cmd_payload & 0b1
    data_rate_ack = cmd_payload >> 1 & 0b1
    power_ack = cmd_payload >> 2 & 0b1
    rfu = cmd_payload >> 3
    if channel_mask_ack & data_rate_ack & power_ack == 1:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='LinkADRAns Success: %s, power_ack: %d, channel_mask_ack: %d, data_rate_ack: %d' % (cmd_payload, power_ack, channel_mask_ack, data_rate_ack))
    else:
        Logger.error(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                     msg='LinkADRAns Fail: %s, power_ack: %d, channel_mask_ack: %d, data_rate_ack: %d' % (cmd_payload, power_ack, channel_mask_ack, data_rate_ack))

    

def analyze_DutyCycleAns(device, cmd_payload):
    assert len(cmd_payload) == 0, 'WRONG MAC CMD PAYLOAD OF DutyCycleAns'
    DevInfo(device.dev_eui).p_to_c('MaxDutyCycle')
    Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                msg='DutyCycleAns Success: %s' % cmd_payload)


def analyze_RXParamSetupAns(device, cmd_payload):
    assert len(cmd_payload) == 1, 'WRONG MAC CMD PAYLOAD OF RXParamSetupAns'
    status = cmd_payload[0]
    channel_ack = status & 0b1
    RX2DataRate_ack = status >> 1 & 0b1
    RX1DRoffset_ack = status >> 2 & 0b1
    rfu = status >> 3
    if channel_ack & RX1DRoffset_ack & RX2DataRate_ack == 1:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='RXParamSetupAns Success: %s' % cmd_payload)
        DevInfo(device.dev_eui).p_to_c('RX1DRoffset', 'RX2DataRate', 'RX2Frequency')
    else:
        Logger.error(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                     msg='RXParamSetupAns Fail: %s, channel_ack: %d, RX1DRoffset_ack: %d, RX2DataRate_ack: %d' % (cmd_payload, channel_ack, RX1DRoffset_ack, RX2DataRate_ack))


def analyze_DevStatusAns(device, cmd_payload):
    """
    battery == 0        mean the end-device is connected to an external power source.
    battery == 1~254    mean the battary level,1 being at minimum and 254 being at maximum.
    battery == 255      mean the end-device was not able to measure the battery level.
    """
    assert len(cmd_payload) == 2, 'WRONG MAC CMD PAYLOAD OF DevStatusAns'
    battery = cmd_payload[0]
    margin = cmd_payload[1]
    snr_ = margin & 0b111111    # 6 bit signed int
    if snr_ > 31:
        snr_ |= 0b11000000
    # ！！！！！！！！！！！！！！！ why use ctypes?
    snr = ctypes.c_int8(snr_).value
    rfu = margin >> 6
    Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                msg='DevStatusAns Success: %s, battery: %d, margin: %d, snr: %d' % (cmd_payload, battery, margin, snr))
    DevInfo(device.dev_eui).set_value(battery=battery, snr=snr)


def analyze_NewChannelAns(device, cmd_payload):
    assert len(cmd_payload) == 1, 'WRONG MAC CMD PAYLOAD OF NewChannelAns'
    # logger.info(ConstLog.mac_cmd+'analyze_NewChannelAns')
    status = cmd_payload[0]
    ch_ack = status & 0b1
    dr_ack = status >> 1 & 0b1
    rfu = status >> 2
    if ch_ack & dr_ack == 1:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='DevStatusAns Success: %s, ch_ack: %d, dr_ack: %d' % (cmd_payload, ch_ack, dr_ack))
    else:
        Logger.error(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                     msg='DevStatusAns Fail: %s, ch_ack: %d, dr_ack: %d' % (cmd_payload, ch_ack, dr_ack))


def analyze_RXTimingSetupAns(device, cmd_payload):
    assert len(cmd_payload) == 0, 'WRONG MAC CMD PAYLOAD OF RXTimingSetupAns'
    Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                msg='RXTimingSetupAns Success: %s' % cmd_payload)
    DevInfo(device.dev_eui).p_to_c('RxDelay')


def analyze_PingSlotInfoReq(device, cmd_payload):
    assert len(cmd_payload) == 1, "WRONG MAC CMD PAYLOAD OF PingSlotInfoReq"
    datr = cmd_payload[0] & 0b1111
    periodicity = cmd_payload[0] >> 4 & 0b111
    rfu = cmd_payload[0] >> 7
    Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                msg='PingSlotInfoReq: %s, datr: %s, periodicity: %s' % (cmd_payload, datr, periodicity))
    ClassBInfo(ConstDB0.dev + hexlify(device.dev_eui).decode(), datr, periodicity).set()
    #sent ans back
    ping_slot_info_ans = MACCmd(device.dev_eui)
    ping_slot_info_ans.push_into_que(cid=CID.PingSlotInfoAns)


def analyze_PingSlotFreqAns(device, cmd_payload):
    assert len(cmd_payload) == 1, "WRONG MAC CMD PAYLOAD OF PingSlotFreqAns"
    status = cmd_payload[0]
    ch_ack = status & 0b1
    dr_ack = status >> 1 & 0b1
    rfu = status >> 2
    if ch_ack & dr_ack == 1:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='PingSlotFreqAns Success: %s, ch_ack: %s, dr_ack: %s' % (cmd_payload, ch_ack, dr_ack))
    else:
        Logger.error(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='PingSlotFreqAns Fqil: %s, ch_ack: %s, dr_ack: %s' % (cmd_payload, ch_ack, dr_ack))


def analyze_BeaconTimingReq(device, cmd_payload):
    assert len(cmd_payload) == 0, "WRONG MAC CMD PAYLOAD OF BeaconTimingReq"
    Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                msg='BeaconTimingReq: %s' % cmd_payload)
    ##action ---- get the next beacon timing and channel

    delay = BeaconTiming.cal_beacon_time_delay(device)
    channel = 0

    ##gen payload
    mac_cmd_payload = BeaconTimingAns(delay, channel).return_data()
    beacon_timing_ans = MACCmd(device.dev_eui)
    beacon_timing_ans.push_into_que(CID.BeaconTimingAns, payload=mac_cmd_payload)


def analyze_BeaconFreqAns(device, cmd_payload):
    assert len(cmd_payload) == 1, "WRONG MAC CMD PAYLOAD OF BeaconFreqAns"
    status = cmd_payload[0]
    freq_ack = status & 0b1
    rfu = status >> 1
    if freq_ack == 1:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='BeaconFreqAns: %s, freq_ack: %s' % (cmd_payload, freq_ack))
    else:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='BeaconFreqAns: %s, freq_ack: %s' % (cmd_payload, freq_ack))


def analyze_DlChannelAns(device, cmd_payload):
    freq_ok = cmd_payload & 0b1
    up_freq_exist = cmd_payload >> 1
    if freq_ok and up_freq_exist:
        Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                    msg='DlChannelAns: %s, freq_ok: %s, up_freq_exist: %s' % (cmd_payload, freq_ok, up_freq_exist))

# def do_default(*nkw):
#     Logger.error(action=Action.mac_cmd_get, )

#switch the analye function which analyze the given cmd_payload according to CID
# @debuger('cid switch')
# @timeStumpFunc('cid_switch')


def cid_switch(device, cid, cmd_payload):
    switcher = {
        2: analyze_LinkCheckReq,
        3: analyze_LinkADRAns,
        4: analyze_DutyCycleAns,
        5: analyze_RXParamSetupAns,
        6: analyze_DevStatusAns,
        7: analyze_NewChannelAns,
        8: analyze_RXTimingSetupAns,
        16: analyze_PingSlotInfoReq,
        17: analyze_PingSlotFreqAns,
        18: analyze_BeaconTimingReq,
        19: analyze_BeaconFreqAns,
    }
    return switcher[cid](device, cmd_payload)


# @debuger('analyze_mac_cmd_ans')
# @timeStumpFunc('analyze_mac_cmd_ans')
def analyze_mac_cmd_ans(device, mac_cmd):
    """
    :param mac_fhdr_fopts: bytes
    :return:dict
    """
    while len(mac_cmd) != 0:
        cid = mac_cmd[0]
        try:
            if 128 <= cid <= 255:
                Logger.info(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg='Proprietary MAC CMD:% cid' % cid)
                return
            cmd_payload_len = MACConst.mac_cmd_up_len[cid]
            cmd_payload = mac_cmd[1:cmd_payload_len+1]
            mac_cmd = mac_cmd[cmd_payload_len+1:]
            cid_switch(device, cid, cmd_payload)
        except KeyError as error:
            Logger.error(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg='ERROR: %s' % error)
            return
        except AssertionError as error:
            Logger.error(action=Action.mac_cmd_get, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg='ERROR: %s' % error)
            return