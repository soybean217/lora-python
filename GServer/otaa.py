from utils.db1 import db1, Channel1
from utils.db0 import db0, ConstDB0
from const import Const
from utils.exception import AccessDeny, ReadOnlyDeny
from binascii import hexlify, a2b_base64
import json
from gevent import Greenlet, sleep
from utils.log import Logger, Action, IDType
from object.application import Application
import time
from frequency_plan import frequency_plan
from utils.redis_lock import start_device_block, get_device_block_info
from object.otaa_object import JoinDevGateway, JoinTransParams, JoiningDev, OTAAMsg, OTAAMsgDn
from object.gateway import Gateway, PullInfo
from utils.utils import get_random_token

OTAA_EXPIRE = 5


class OTAAConst:
    dev_nonce = 'DEV_NONCE:'



class DevNonce:
    @staticmethod
    def add(dev_eui, nonce):
        return db1.sadd(OTAAConst.dev_nonce + hexlify(dev_eui).decode(), nonce)

    @staticmethod
    def delete(dev_eui):
        db1.delete(OTAAConst.dev_nonce + hexlify(dev_eui).decode())

    @staticmethod
    def exists(dev_eui, nonce):
        return db1.sismember(OTAAConst.dev_nonce + hexlify(dev_eui).decode(), nonce)


class OTAAJoin(Greenlet):
    def __init__(self, request_msg, trans_params, gateway):
        """
        :param request_msg:str
        :param trans_params:dict
        :param gateway_mac_addr:
        :return:
        """
        Greenlet.__init__(self)
        app_eui = int.to_bytes(int.from_bytes(request_msg[1:9], byteorder='little'), byteorder='big', length=8)
        dev_eui = int.to_bytes(int.from_bytes(request_msg[9:17], byteorder='little'), byteorder='big', length=8)
        dev_nonce = int.to_bytes(int.from_bytes(request_msg[17:19], byteorder='little'), byteorder='big', length=2)
        mic = request_msg[19:23]
        hex_dev_eui = hexlify(dev_eui).decode()
        hex_app_eui = hexlify(app_eui).decode()
        Logger.info(action=Action.otaa, type=IDType.device, id=dev_eui, msg="JOIN REQ: APP:%s, dev_nonce:%s" % (hex_app_eui, dev_nonce))
        real_app_eui = db0.hget(ConstDB0.dev + hex_dev_eui, 'app_eui')
        if real_app_eui is not None and real_app_eui != app_eui:
            raise Exception('Device %s belong to other app %s, not app %s' % (dev_eui, real_app_eui, app_eui))
        else:
            app = Application.objects.get(app_eui)
        if app is None:
            raise KeyError('APP:%s does not exist' % hex_app_eui)
        elif gateway.public is not True and app.user_id != gateway.user_id:
            raise AccessDeny(hexlify(gateway.mac_addr).decode(), ConstDB0.app + hex_app_eui)
        self.app = app
        self.dev_eui = dev_eui
        self.request_msg = request_msg
        self.trans_params = trans_params
        self.gateway = gateway
        self.dev_nonce = dev_nonce
        self.mic = mic

    def run(self):
        ts = round(time.time())
        dev_gateway = JoinDevGateway(self.dev_eui, self.gateway.mac_addr, int(self.trans_params['rssi']), float(self.trans_params['lsnr']))
        hex_dev_eui = hexlify(self.dev_eui).decode()
        if start_device_block(hex_dev_eui, data=self.dev_nonce, lock_timeout=5):
            dev_gateway.set()
            trans_params = JoinTransParams(self.dev_eui, gateway_mac_addr=self.gateway.mac_addr, trans_params=self.trans_params, ts=ts)
            trans_params.save()
            Logger.info(action=Action.otaa, type=IDType.device, id=hex_dev_eui, msg='New Message from GATEWAY:%s, dev_nonce:%s' % (hexlify(self.gateway.mac_addr).decode(), hexlify(self.dev_nonce).decode()))
        else:
            dev_nonce = get_device_block_info(hex_dev_eui)
            if self.dev_nonce != dev_nonce:
                Logger.error(action=Action.otaa, type=IDType.device, id=hex_dev_eui, msg='In device otaa block, another otaa request come. dev_nonce:%s' % self.dev_nonce)
                return
            if dev_gateway.add():
                trans_params = JoinTransParams(self.dev_eui, gateway_mac_addr=self.gateway.mac_addr, trans_params=self.trans_params, ts=ts)
                trans_params.save()
            Logger.info(action=Action.otaa, type=IDType.device, id=hex_dev_eui, msg='Send by other GATEWAY:%s, dev_nonce:%s' % (hexlify(self.gateway.mac_addr).decode(), hexlify(self.dev_nonce).decode()))
            return
        nonce_first_use = DevNonce.add(self.dev_eui, self.dev_nonce)
        if not nonce_first_use:
            Logger.error(action=Action.otaa, type=IDType.device, id=hex_dev_eui, msg='dev_nonce %s already used' % self.dev_nonce)
            return
        # join_device = JoiningDev(app_eui=self.app.app_eui, dev_eui=self.dev_eui, dev_nonce=self.dev_nonce, mic=self.mic, time=time.time())
        # join_device.save()
        sleep(0.1)
        gateway_mac_addr = JoinDevGateway.get_best_mac_addr(self.dev_eui)
        trans_params = JoinTransParams.objects.get(self.dev_eui, gateway_mac_addr)
        msg = OTAAMsg(self.dev_eui, self.app.app_eui, self.request_msg,
                      dl_settings=self.__dl_settings(),
                      rx_delay=self.__rx_delay(),
                      cf_list=self.__cf_list(),
                      trans_params=trans_params,
                      ts=ts)
        msg.publish()

    def __rx_delay(self):
        FREQ_PLAN = frequency_plan[self.app.freq_plan]
        rx_delay = bytes([FREQ_PLAN.RxDelay])
        return rx_delay

    def __dl_settings(self):
        FREQ_PLAN = frequency_plan[self.app.freq_plan]
        # RX1DRoffset default is 0
        dl_settings = bytes([(0 << 4) + FREQ_PLAN.RX2DataRate])
        return dl_settings

    def __cf_list(self):
        FREQ_PLAN = frequency_plan[self.app.freq_plan]
        cf_list = FREQ_PLAN.Channel.CF_LIST
        return cf_list


def write_join_accept_data(dev_eui, data):
    join_device = JoiningDev.objects.get(dev_eui)
    if join_device:
        mac_addr_list = JoinDevGateway.list_mac_addr_by_score(dev_eui)
        for mac_addr in mac_addr_list:
            gateway = Gateway.objects.get(mac_addr)
            trans_params = JoinTransParams.objects.get(dev_eui, gateway.mac_addr)
            pull_info = PullInfo.objects.get_pull_info(gateway.mac_addr)
            if len(trans_params) > 0 and pull_info is not None:
                txpk = pack_join_accept_data(trans_params, data, join_device.app.freq_plan)
                json_data = {'txpk': txpk}
                prot_ver = bytes([pull_info.prot_ver])
                packet = prot_ver + get_random_token() + Const.PULL_RESP_IDENTIFIER
                packet = packet + json.dumps(json_data).encode()
                msg_dn = OTAAMsgDn(app_eui=join_device.app.app_eui, dev_eui=join_device.dev_eui, trans_params=txpk, ts=time.time())
                msg_dn.publish()
                return packet, pull_info
    else:
        Logger.error(action=Action.otaa, type=IDType.device, id=dev_eui, msg='JoiningDev does not exists')


def pack_join_accept_data(trans_parms, data, freq_plan):
    FREQ_PLAN = frequency_plan[freq_plan]
    txpk = {}
    txpk['rfch'] = FREQ_PLAN.RF_CH    # rossi support
    txpk['powe'] = 14
    txpk['modu'] = trans_parms['modu']
    if txpk['modu'] == 'LORA':
        txpk['codr'] = trans_parms['codr']
        txpk['ipol'] = True     # rossi support
    elif txpk['modu'] == 'FSK':
        txpk['fdev'] = 3000
    txpk['prea'] = 8
    txpk['size'] = len(a2b_base64(data))
    txpk['data'] = data
    txpk['ncrc'] = False    # unconfirm
    datr = FREQ_PLAN.DataRate[trans_parms['datr']]
    txpk['datr'] = FREQ_PLAN.rx1_datr(datr.value, 0).name
    txpk['freq'] = FREQ_PLAN.rx1_freq(float(trans_parms['freq']))
    txpk['tmst'] = int(trans_parms['tmst']) + FREQ_PLAN.JOIN_ACCEPT_DELAY * 1000000
    return txpk