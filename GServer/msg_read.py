from binascii import a2b_base64, hexlify
import binascii
from struct import unpack
from const import Const, MType
from utils.lora_crypto import LoRaCrypto
from mac_cmd.adr import ADR
from mac_cmd.mac_cmd_analyze import analyze_mac_cmd_ans
from object.message import MsgUp
from object.device import DeviceACK, ACKName, Device
from object.fields import ClassType
from object.trans_params import TransParams, DevGateway
from object.retransmission import Resend
from object.gateway import Gateway, GatewayStatus
from otaa import OTAAJoin
import time
from utils.log import Logger, Action, IDType
from utils.db0 import db0, Channel0
from utils.utils import endian_reverse, iso_to_utc_ts
from gevent import Greenlet, sleep
from utils.redis_lock import start_device_block
from utils.timing_log import timing
from datetime import datetime


def read_push_data(json_data, gateway, *args):
    if isinstance(json_data, dict):
        if 'rxpk' in json_data:
            for data_raw in json_data['rxpk']:
                gateway.frequency_statistics(data_raw['freq'])
                data = base64_decode(data_raw.pop('data'))
                if data is not None:
                    major = data[0] & 0b11
                    if major != 0:
                        Logger.error(action=Action.uplink, msg='ERROR: Major != 0, Major = %s' % major)
                        continue
                    mtype = data[0] >> 5
                    if mtype == MType.JOIN_REQUEST:
                        try:
                            otaa = OTAAJoin(request_msg=data, trans_params=data_raw, gateway=gateway)
                            otaa.start()
                        except Exception as error:
                            Logger.error(action=Action.otaa, msg='REQUEST: %s; ERROR: %s' % (data, error))
                    elif mtype == MType.UNCONFIRMED_DATA_UP or mtype == MType.CONFIRMED_DATA_UP:
                        dev_addr = endian_reverse(data[1:5])
                        device = Device.objects.get_device_by_addr(dev_addr)
                        if device is None:
                            Logger.error(action=Action.data_up, type=IDType.dev_addr, id=hexlify(dev_addr).decode(), msg='Can\'t Find Device for this DevAddr')
                            continue
                        if gateway.public is not True and device.app.user_id != gateway.user_id:
                            Logger.error(action=Action.data_up, msg='Gateway %s is not Public and device % s is not belong to the same user' % (gateway.mac_addr, device.dev_eui))
                            continue
                        ReadDataUp(device.dev_eui, gateway, data_raw, mtype, data, *args).start()
                    elif mtype == MType.PTY:
                        dev_addr == endian_reverse(data[1:5])
                        device = Device.objects.get_device_by_addr(dev_addr)
                        if device is None:
                            Logger.error(action=Action.proprietary, type=IDType.dev_addr, id=hexlify(dev_addr).decode(), msg='Can\'t Find Device for this DevAddr')
                        ReadPTY(dev_eui=device.dev_eui, gateway=gateway, trans_params=data_raw, mtype=mtype, data=data).start()
        if 'stat' in json_data:
            stat = json_data['stat']
            gateway_stat = GatewayStatus(gateway.mac_addr, stat['lati'], stat['long'], stat['alti'])
            gateway_stat.save()


class ReadPTY(Greenlet):
    def __init__(self, dev_eui, gateway, trans_params, mtype, data):
        Greenlet.__init__(self)
        self.dev_eui = dev_eui
        self.mtype = mtype
        self.data = data
        self.gateway = gateway
        self.trans_params = trans_params
        self.trans_params['s_time'] = time.time()

    def _run(self):
        ts = round(time.time())
        data = self.data
        device = Device.objects.get(self.dev_eui)
        fcnt = unpack('<H', data[6:8])[0]
        device.fcnt_up = fcnt
        dev_gateway = DevGateway(device.dev_eui, self.gateway.mac_addr, int(self.trans_params['rssi']), float(self.trans_params['lsnr']))
        if start_device_block(self.dev_eui):
            dev_gateway.set()
            Logger.info(action=Action.uplink, type=IDType.device, id=device.dev_eui, msg='Fcnt: %s; New Message from gateway: %s' % (device.fcnt_up, hexlify(self.gateway.mac_addr).decode()))
            trans_params = TransParams(device.dev_eui, gateway_mac_addr=self.gateway.mac_addr, trans_params=self.trans_params, ts=ts)
            trans_params.save()
        else:
            Logger.info(action=Action.uplink, type=IDType.device, id=device.dev_eui, msg='Fcnt: %s; Send by other gateway: %s' % (device.fcnt_up, hexlify(self.gateway.mac_addr).decode()))
            if dev_gateway.add():
                trans_params = TransParams(device.dev_eui, gateway_mac_addr=self.gateway.mac_addr, trans_params=self.trans_params, ts=ts)
                trans_params.save()
            return
        if fcnt == device.fcnt_up:
            retransmission = 1
        else:
            retransmission = 0
            device.update()
        fctrl = data[5]
        fport = 0
        app_data = b''
        if len(data) > 8:
            fport = data[8]
            app_data = data[8: -1]
        sleep(0.1)
        gateway_mac_addr = Gateway.objects.best_mac_addr(device.dev_eui)
        trans_params = TransParams.objects.get(device.dev_eui, gateway_mac_addr)
        msg = MsgUp(device.dev_eui, ts=ts, fcnt=device.fcnt_up, port=fport, data=app_data,
                    mtype=self.mtype, retrans=retransmission, trans_params=trans_params, cipher=False, )
        msg.save()
        Logger.info(action=Action.uplink, type=IDType.device, id=device.dev_eui,
                    msg='fcnt:%s, mtype: %s; retransmission: %s; fport: %s; app_data: %s'
                        % (device.fcnt_up, MType(self.mtype).name, retransmission, fport, app_data))
        db0.publish(Channel0.rx1_alarm, device.dev_eui)


class ReadDataUp(Greenlet):
    def __init__(self, dev_eui, gateway, trans_params, mtype, data, *args):
        Greenlet.__init__(self)
        self.dev_eui = dev_eui
        self.mtype = mtype
        self.data = data
        self.gateway = gateway
        self.trans_params = trans_params
        self.trans_params['s_time'] = time.time()
        self.args = list(args)

    def run(self):
        data = self.data
        device = Device.objects.get(self.dev_eui)
        ts = round(time.time())
        restart = False
        try:
            addr_int = unpack(">I", device.addr)[0]
            mac_fhdr_fcnt = data[6:8]
            mic = data[len(data)-4:]
            fcnt_d = device.fcnt_up
            fcnt_m = unpack('<H', mac_fhdr_fcnt)[0]
            if not mic_ver(data[0:len(data)-4], device.nwkskey, addr_int, Const.DIR_UP, fcnt_m, mic):
                low_16 = fcnt_d & 0xffff
                high_16 = fcnt_d >> 16
                low_16 = fcnt_m
                if low_16 < fcnt_m:
                    high_16 += 1
                fcnt_m = (high_16 << 16) + low_16
                if not mic_ver(data, device.nwkskey, addr_int, Const.DIR_UP, fcnt_m, mic):
                    raise MICError()
            sub = fcnt_m - fcnt_d
            if sub > 0:
                if sub > Const.MAX_FCNT_GAP:
                    if device.check_fcnt:
                        raise FcntError(sub)
            elif sub < 0:
                if fcnt_m > Const.MAX_FCNT_GAP:
                    if device.check_fcnt:
                        raise FcntError(sub)
                if fcnt_m < 10:
                    device.fcnt_down = 0
                    restart = True
            # new_fcnt_tuple = up_cnt(mac_fhdr_fcnt, device.fcnt_up, device.check_fcnt)
            # fcnt_new = mic_verify(data[0:len(data)-4], device.nwkskey, addr_int, new_fcnt_tuple, mic)
        except (FcntError, MICError) as error:
            Logger.error(action=Action.uplink, type=IDType.device, id=device.dev_eui, msg='ERROR: MIC or FCNT: %s' % error)
            return
        except Exception as error:
            print(error)
            Logger.error(action=Action.uplink, type=IDType.device, id=device.dev_eui, msg='Unknown ERROR: %s' % error)
            return
        dev_gateway = DevGateway(device.dev_eui, self.gateway.mac_addr, int(self.trans_params['rssi']), float(self.trans_params['lsnr']))
        if start_device_block(self.dev_eui):
            dev_gateway.set()
            Logger.info(action=Action.uplink, type=IDType.device, id=device.dev_eui, msg='Fcnt: %s; New Message from gateway: %s' % (fcnt_m, hexlify(self.gateway.mac_addr).decode()))
            trans_params = TransParams(device.dev_eui, gateway_mac_addr=self.gateway.mac_addr, trans_params=self.trans_params, ts=ts)
            trans_params.save()
        else:
            Logger.info(action=Action.uplink, type=IDType.device, id=device.dev_eui, msg='Fcnt: %s; Send by other gateway: %s' % (fcnt_m, hexlify(self.gateway.mac_addr).decode()))
            if dev_gateway.add():
                trans_params = TransParams(device.dev_eui, gateway_mac_addr=self.gateway.mac_addr, trans_params=self.trans_params, ts=ts)
                trans_params.save()
            return
        if fcnt_m == fcnt_d:
            retransmission = 1
        else:
            retransmission = 0
            device.fcnt_up = fcnt_m
            device.update()
        fctrl = data[5]
        foptslen = fctrl & 0b1111
        class_b = fctrl >> 4 & 0b1
        ack = fctrl >> 5 & 0b1
        adrackreq = fctrl >> 6 & 0b1
        adr = fctrl >> 7
        mac_cmd = data[8:8+foptslen]
        encrypt = False
        fport = 0
        app_data = b''
        if (8 + foptslen) < len(data)-4:
            fport = data[8 + foptslen]
            frampayload = data[9 + foptslen: len(data)-4]
            assert -1 < fport < 256, "AssertError: fport error"
            if fport == 0:
                mac_cmd = LoRaCrypto.payload_decrypt(frampayload, device.nwkskey, addr_int, Const.DIR_UP, fcnt_m)
            else:
                if device.appskey == b'':
                    encrypt = True
                    app_data = frampayload
                elif len(device.appskey) == 16:
                    app_data = LoRaCrypto.payload_decrypt(frampayload, device.appskey, addr_int, Const.DIR_UP, fcnt_m)
        if class_b == 1:
            if device.dev_class == ClassType.a:
                device.dev_class = ClassType.b
        else:
            if device.dev_class == ClassType.b:
                device.dev_class = ClassType.a
        device.update()
        if ack == 1:    # if ack == 1, confirm the down link which need to be confirm
            Resend(device.dev_eui).del_retrans_down()
        if adrackreq == 1:
            DeviceACK(device.dev_eui, ACKName.adr_ack_req).set(1)
        if self.mtype == MType.CONFIRMED_DATA_UP:
            DeviceACK(device.dev_eui, ACKName.ack_request).set(1)
        # analyze mac cmd
        analyze_mac_cmd_ans(device, mac_cmd)
        # ADR
        if adr and device.adr:
            adr_thread = ADR(device)
            adr_thread.start()
        # sleep(0.1)
        gateway_mac_addr = Gateway.objects.best_mac_addr(device.dev_eui)
        trans_params = TransParams.objects.get(device.dev_eui, gateway_mac_addr)
        msg = MsgUp(device.dev_eui, ts=ts, fcnt=device.fcnt_up, port=fport, data=app_data, cipher=encrypt,
                    mtype=self.mtype, retrans=retransmission, trans_params=trans_params, restart=restart)
        msg.save()
        Logger.info(action=Action.uplink, type=IDType.device, id=device.dev_eui,
                    msg='fcnt:%s, mtype: %s; retransmission: %s; ack: %s; adrackreq: %s; mac_cmd: %s; class_b: %s; fport: %s; app_data: %s; encrypt: %s '
                    % (device.fcnt_up, MType(self.mtype).name, retransmission, ack, adrackreq, mac_cmd, class_b, fport, app_data, encrypt))
        db0.publish(Channel0.rx1_alarm, device.dev_eui)
        t2 = time.time()
        g_time = iso_to_utc_ts(self.trans_params['time'])
        self.args.insert(0, g_time)
        self.args.append(t2)
        timing.info(msg='PUSH_DATA: DEV:%s, FCNT:%s, DELAY_TIME:%s, TIME:%s' % (hexlify(device.dev_eui).decode(), fcnt_m, self.args[1] - self.args[0], self.args))



def mic_ver(data, nwkskey, addr_int, dir, fcnt, mic):
    mic_compute = LoRaCrypto.compute_mic(data, nwkskey, addr_int, dir, fcnt)
    if mic_compute == mic:
        return True
    else:
        return False


def up_cnt(fcnt_msg, fcnt_dev, strict_check):
    assert len(fcnt_msg) == 2, 'fcnt_msg length error'
    fcnt_msg = unpack('<H', fcnt_msg)[0]
    low_16 = fcnt_dev & 0xffff
    high_16 = fcnt_dev >> 16
    sub = fcnt_msg - low_16
    if sub > 0:
        if sub > Const.MAX_FCNT_GAP:
            raise FcntError(sub)
        low_16 = fcnt_msg
        fcnt_dev = (high_16 << 16) + low_16
        return fcnt_dev, fcnt_msg
    else:
        if strict_check == 1 or fcnt_msg > Const.MAX_FCNT_GAP:
            if sub == 0:
                return fcnt_dev,
            if sub > (Const.MAX_FCNT_GAP - 0x10000):
                raise FcntError(sub)
            low_16 = fcnt_msg
            high_16 += 1
            fcnt_dev = (high_16 << 16) + low_16
            return fcnt_dev,
        elif strict_check == 0 and fcnt_msg <= Const.MAX_FCNT_GAP:
            if sub == 0:
                return fcnt_dev, fcnt_msg
            if sub > (Const.MAX_FCNT_GAP - 0x10000):
                return fcnt_msg,
            low_16 = fcnt_msg
            high_16 += 1
            fcnt_dev = (high_16 << 16) + low_16
            return fcnt_dev, fcnt_msg


def mic_verify(data, nwkskey, addr, fcnt, mic):
    """
    :param data: bytes
    :param nwkskey: bytes
    :param addr: int
    :param dir: Const.DIR_UP or Const.DIR_DOWN
    :param fcnt: tuple
    :param mic: bytes
    :return:
    """
    len_fcnt = len(fcnt)
    if len_fcnt == 1:
        mic_compute = LoRaCrypto.compute_mic(data, nwkskey, addr, Const.DIR_UP, fcnt[0])
        if mic_compute == mic:
            return fcnt[0]
        else:
            Logger.error(action=Action.mic, msg='fcnt:%s, data:%s, nwkskey:%s, addr:%s, dir_up:%s, mic_compute:%s, mic:%s' % (fcnt[0],data,nwkskey,addr,Const.DIR_UP, mic_compute,mic))
            raise MICError()
    elif len_fcnt == 2:
        mic_compute = LoRaCrypto.compute_mic(data, nwkskey, addr, Const.DIR_UP, fcnt[0])
        if mic_compute == mic:
            return fcnt[0]
        else:
            mic_compute = LoRaCrypto.compute_mic(data, nwkskey, addr, Const.DIR_UP, fcnt[1])
            if mic_compute == mic:
                return fcnt[1]
            else:
                Logger.error(action=Action.mic, msg='fcnt:%s, data:%s, nwkskey:%s, addr:%s, dir_up:%s, mic_compute:%s, mic:%s' % (fcnt[1],data,nwkskey,addr,Const.DIR_UP, mic_compute,mic))
                raise MICError()
    else:
        raise AssertionError('mic_verify Error')


def base64_decode(data):
    missing_padding = 4 - len(data) % 4
    if missing_padding:
        data += '=' * missing_padding
    try:
        return a2b_base64(data)
    except binascii.Error:
        Logger.error(action=Action.rxpk, msg='Invalid base64 string: %s' % data)
        return None


class FcntError(Exception):
    def __init__(self, fcnt):
        self.fcnt = fcnt

    def __str__(self):
        return 'Fcnt exceed MAX_FCNT_GAP'


class MICError(Exception):
    def __str__(self):
        return 'MIC Error'

