import json
from binascii import hexlify, b2a_base64
from const import Const, MType
from object import ACKName, DeviceACK, Device
from object import ClassType
from object import DownLinkUni, DownLinkMulti
from object import Gateway, PullInfo
from object import TransParams
from object import Resend
from object import BTiming
from object.trans_params import DnTransParams
from mac_cmd.mac_cmd_gen import MACCmd
from utils.log import Logger, Action, IDType
from utils.db0 import ConstDB0
import time
from utils.utils import iso_to_utc_ts
from datetime import datetime
from frequency_plan import frequency_plan
from object.message import MsgDn
from utils.utils import get_random_token


def write_push_ack(token, protocol_ver):
    assert len(token) == 2, 'AssertError: Write_Push_Ack Token Error'
    if isinstance(protocol_ver, int):
        protocol_ver = bytes([protocol_ver])
    return protocol_ver + token + Const.PUSH_ACK_IDENTIFIER


def write_pull_ack(protocol_ver, token, disable, restart=False):
    assert len(token) == 2, 'AssertError: Write_Push_Ack Token Error'
    if isinstance(protocol_ver, int):
        protocol_ver = bytes([protocol_ver])
    if disable == 1:
        return protocol_ver + token + Const.PULL_ACK_IDENTIFIER + Const.IGNORE_DATA + bytes([restart.real])
    else:
        return protocol_ver + token + Const.PULL_ACK_IDENTIFIER + Const.PROCESS_DATA + bytes([restart.real])


def write_pull_resp(device, rx_window):
    data = None
    resend = Resend(device.dev_eui)
    resend_data = resend.get_resend_data().get(b'data', None)
    # if resend_data is None,
    maxcnt = resend.update_repeat_cnt() if resend_data else -1
    retransmission = False
    if maxcnt > 0:
        data = resend_data
        retransmission = True
        Logger.info(action=Action.downlink, type=device, id=hexlify(device.dev_eui).decode(), msg='Resend_data: %s' % data)
    else:
        if maxcnt == 1 or maxcnt == 0:
            resend.del_retrans_down()
        if device.dev_class == ClassType.c and rx_window == 1:
            fport_frampayload = device.que_down.pop(class_c_rx1=1)
        else:
            fport_frampayload = device.que_down.pop()
        ack = DeviceACK(device.dev_eui, ACKName.ack_request).get()
        # 51 lest max len of EU868 51
        len_fport_frampayload = 0
        if fport_frampayload is not None:
            len_fport_frampayload = len(fport_frampayload)
        max_len = Const.EU868_MAX_PAYLOAD_LEN - len_fport_frampayload + 1
        mac_cmd = MACCmd(device.dev_eui).pop_from_que(max_len)
        if (fport_frampayload is not None) or (ack == 1) or len(mac_cmd) > 0:
            mtype = MType.UNCONFIRMED_DATA_DOWN
            if fport_frampayload is not None:
                settings = fport_frampayload[0]
                cipher = settings >> 7
                msg_rx_window = settings >> 5 & 0b011
                if msg_rx_window != 0:
                    rx_window = msg_rx_window
                confirmed = settings >> 4 & 0b0001
                if confirmed == 1:
                    mtype = MType.CONFIRMED_DATA_DOWN
                fport = fport_frampayload[1]
                frmpayload = fport_frampayload[2:]
            else:
                cipher = None
                fport = None
                frmpayload = b''
            if len(mac_cmd) > 0:
                pass
            if ack == 1:
                DeviceACK(device.dev_eui, ACKName.ack_request).set(0)
            if device.que_down.len() > 0:
                fpending = 1
            else:
                fpending = 0
            Logger.info(action=Action.downlink, type=IDType.device, id=hexlify(device.dev_eui).decode(),
                        msg='FPORT_FRAMPAYLOAD: %s, MAC_CMD: %s, ACK: %s, fpending: %s, mtype: %s' % (fport_frampayload, mac_cmd, ack, fpending, mtype))
            device.fcnt_down += 1
            data = DownLinkUni(device,
                               mtype=mtype,
                               fpending=fpending,
                               ack=ack,
                               adrackreq=0,
                               mac_command=mac_cmd,
                               cipher=cipher,
                               fport=fport,
                               frmpayload=frmpayload).pack_data()
            device.update()
    if data is not None:
        gateway_list = Gateway.objects.list_order_by_score(device.dev_eui)
        for gateway in gateway_list:
            trans_params = TransParams.objects.get(device.dev_eui, gateway.mac_addr)
            pull_info = PullInfo.objects.get_pull_info(mac_addr=gateway.mac_addr)
            if len(trans_params) > 0 and pull_info is not None:
                txpk, s_time = pack_down_data(trans_params, data, rx_window, device)
                s_time = round(s_time)
                s_time = round(time.time())
                prot_ver = bytes([pull_info.prot_ver])
                packet = prot_ver + get_random_token() + Const.PULL_RESP_IDENTIFIER
                packet = packet + json.dumps({'txpk': txpk}).encode()
                # if retransmission is True:
                message = MsgDn(category=ConstDB0.dev, eui=hexlify(device.dev_eui).decode(), ts=s_time,
                                fcnt=device.fcnt_down, datr=txpk['datr'], freq=txpk['freq'], gateways=gateway.mac_addr)
                #----------------add---------------
                dn_trans_params = DnTransParams(category=ConstDB0.dev, eui=hexlify(device.dev_eui).decode(), gateway_mac_addr=gateway.mac_addr, trans_params=txpk, ts=s_time)
                dn_trans_params.save()
                #----------------add---------------
                # else:
                #     message = MsgDn(category=ConstDB0.dev, eui=hexlify(device.dev_eui).decode(), ts=int(time.time()), fcnt=device.fcnt_down,
                #                     datr=txpk['datr'], freq=['freq'])
                message.save()
                return packet, device.fcnt_down, pull_info
        Logger.error(action=Action.downlink, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg='NO GATEWAY IS AVAILABLE')
    else:
        Logger.info(action=Action.downlink, type=IDType.device, id=hexlify(device.dev_eui).decode(), msg='NO DATA NEED TO BE SEND')


def pack_down_data(trans_parms, data, rx_window, device):
    FREQ_PLAN = frequency_plan[device.app.freq_plan]
    tx_params = device.get_tx_params()
    s_time = 0
    txpk = {}
    txpk['rfch'] = FREQ_PLAN.RF_CH
    txpk['powe'] = 14
    txpk['modu'] = trans_parms['modu']
    if txpk['modu'] == 'LORA':
        txpk['codr'] = trans_parms['codr']
        txpk['ipol'] = True     # rossi support
    # elif txpk['modu'] == 'FSK':
    #     txpk['fdev'] = 3000
    txpk['prea'] = 8
    txpk['size'] = len(data)
    txpk['data'] = b2a_base64(data).decode().rstrip('\n')
    # txpk['ncrc'] = False
    if device.dev_class == ClassType.b:
        b_info = BTiming(ConstDB0.dev + hexlify(device.dev_eui).decode(), time.time())
        s_time = b_info.ping_time()
        txpk['time'] = datetime.utcfromtimestamp(s_time).isoformat() + 'Z'
        txpk['freq'] = FREQ_PLAN.b_freq()
        txpk['datr'] = FREQ_PLAN.DataRate(b_info.datr).name
    elif rx_window == 1:
        datr = FREQ_PLAN.DataRate[trans_parms['datr']]
        txpk['datr'] = FREQ_PLAN.rx1_datr(datr.value, tx_params['RX1DRoffset']).name
        txpk['freq'] = FREQ_PLAN.rx1_freq(float(trans_parms['freq']))
        txpk['tmst'] = int(trans_parms['tmst']) + tx_params['RxDelay'] * 1000000  # 1us step upadd;
        try:
            ts = iso_to_utc_ts(trans_parms['time'])
            s_time = ts + tx_params['RxDelay']
        except Exception as error:
            Logger.error(action=Action.downlink, type=IDType.device, id=device.dev_eui, msg=str(error))
    elif rx_window == 2:
        datr = FREQ_PLAN.DataRate(tx_params['RX2DataRate'])
        txpk['datr'] = datr.name
        txpk['freq'] = tx_params['RX2Frequency']
        if device.dev_class == ClassType.c:
            txpk['imme'] = True
            s_time = time.time()
        elif device.dev_class == ClassType.a:
            txpk['tmst'] = int(trans_parms['tmst']) + (tx_params['RxDelay'] + 1) * 1000000
            try:
                ts = iso_to_utc_ts(trans_parms['time'])
                s_time = ts + tx_params['RxDelay'] + 1
            except Exception as error:
                Logger.error(action=Action.downlink, type=IDType.device, id=device.dev_eui, msg=str(error))
    return txpk, s_time


def write_pull_resp_multi(group):
    if len(group.devices) > 0 and group.app.freq_plan is not None:
        send_gateways_list = set()
        pull_info_set = set()
        devices_has_no_gateway = set()
        class_b = False
        class_c = False
        for dev_eui in group.devices:
            if class_b is False or class_c is False:
                dev_class = Device.objects.get_dev_class(dev_eui)
                if dev_class == ClassType.b:
                    class_b = True
                elif dev_class == ClassType.c:
                    class_c = True
            gateways = Gateway.objects.list_order_by_score(dev_eui)
            pull_info = None
            for gateway in gateways:
                if gateway in send_gateways_list:
                    pull_info = 'Not None'
                else:
                    pull_info = PullInfo.objects.get_pull_info(gateway.mac_addr)
                    if pull_info is not None:
                        send_gateways_list.add(gateway)
                        pull_info_set.add(pull_info)
                        break
            if pull_info is None:
                devices_has_no_gateway.add(dev_eui)
        if len(pull_info_set) > 0:
            fport_frampayload = group.que_down.pop()
            if fport_frampayload is not None:
                text_type = fport_frampayload[0]
                fport = fport_frampayload[1]
                frmpayload = fport_frampayload[2:]
                group.fcnt += 1
                Logger.info(action=Action.downlink, type=IDType.group, id=hexlify(group.id).decode(),
                            msg='fport: %s, frmpayload: %s, fcnt: %s, text_type: %s' % (fport, frmpayload, text_type, group.fcnt))
                data = DownLinkMulti(group,
                                     fpending=0,
                                     text_type=text_type,
                                     fport=fport,
                                     frmpayload=frmpayload,).pack_data()

                packets = []
                if class_c is True:
                    packet_c = pack_down_data_multi(data, dev_class=ClassType.c, id=group.id, frequency=group.app.freq_plan)
                    packets.append(packet_c)
                if class_b is True:
                    packet_b = pack_down_data_multi(data, dev_class=ClassType.b, id=group.id, frequency=group.app.freq_plan)
                    packets.append(packet_b)
                group.update()
                gateways_list = [i_pull_info_set.mac_addr for i_pull_info_set in pull_info_set]

                s_time = round(time.time())
                for gateway_mac in gateways_list:
                    dn_trans_params = DnTransParams(category=ConstDB0.group, eui=hexlify(group.id).decode(),
                                                    gateway_mac_addr=gateway_mac, trans_params=packets[0], ts=s_time)
                    dn_trans_params.save()

                message = MsgDn(category=ConstDB0.group, eui=hexlify(group.id).decode(), ts=s_time,
                                fcnt=group.fcnt, gateways=gateways_list)
                message.save()

                return {'packet': packets,
                        'fcnt': group.fcnt,
                        'pull_info_set': pull_info_set,
                        'ex_devices': devices_has_no_gateway}
            else:
                Logger.info(action=Action.downlink, type=IDType.group, id=hexlify(group.id).decode(), msg='NO DATA NEED TO BE SEND')
        else:
            Logger.error(action=Action.downlink, type=IDType.group, id=hexlify(group.id).decode(), msg='NO GATEWAY IS AVAILABLE')
    else:
        Logger.error(action=Action.downlink, type=IDType.group, id=hexlify(group.id).decode(), msg='NO DEVICE in this GROUP')


def pack_down_data_multi(data, dev_class, id, frequency):
    txpk = {}
    txpk['rfch'] = 0    # rossi support
    txpk['powe'] = 14
    txpk['modu'] = 'LORA'
    txpk['codr'] = '4/5'
    txpk['ipol'] = True  # rossi support
    txpk['prea'] = 8
    txpk['size'] = len(data)
    txpk['data'] = b2a_base64(data).decode().rstrip('\n')
    # txpk['ncrc'] = False
    FREQ_PLAN = frequency_plan[frequency]
    if dev_class == ClassType.c:
        txpk['datr'] = FREQ_PLAN.DataRate(FREQ_PLAN.RX2DataRate).name
        txpk['freq'] = FREQ_PLAN.RX2Frequency
        txpk['imme'] = True
    elif dev_class == ClassType.b:
        b_info = BTiming(ConstDB0.group + hexlify(id).decode(), time.time())
        txpk['time'] = datetime.utcfromtimestamp(b_info.ping_time()).isoformat() + 'Z'
        txpk['freq'] = FREQ_PLAN.b_freq
        txpk['datr'] = FREQ_PLAN.DataRate(b_info.datr).name
    return txpk
    # json_data = {'txpk': txpk}
    # packet = b'\x02' + get_random_token() + Const.PULL_RESP_IDENTIFIER
    # packet = packet + json.dumps(json_data).encode()
    # return packet