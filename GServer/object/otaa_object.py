from object.trans_params import TransParams, DevGateway
from object.application import Application
from utils.db0 import ConstDB0, db0
from utils.db1 import db1, Channel1
from utils.log import Logger, Action, IDType
from binascii import hexlify
import json
import time
from utils.exception import KeyDuplicateError

OTAA_EXPIRE = 5


class OTAAMsg:
    fields = ('dev_eui', 'app_eui', 'request_msg',
              'dl_settings', 'rx_delay', 'cf_list')

    def __init__(self, dev_eui, app_eui, request_msg, dl_settings, rx_delay, cf_list, trans_params, ts=time.time()):
        self.dev_eui = dev_eui
        self.app_eui = app_eui
        self.request_msg = request_msg
        self.dl_settings = dl_settings
        self.cf_list = cf_list
        self.rx_delay = rx_delay
        self.trans_params = trans_params
        self.ts = int(ts)

    def __obj_to_dict(self):
        dd = {}
        for key in self.fields:
            value = hexlify(getattr(self, key)).decode()
            dd[key] = value
        dd['trans_params'] = self.trans_params
        dd['ts'] = self.ts
        return dd

    def publish(self):
        data = json.dumps(self.__obj_to_dict())
        db1.publish(Channel1.join_req_alarm, data)
        db0.publish(Channel1.join_req_alarm +
                    hexlify(self.app_eui).decode(), data)
        Logger.info(action=Action.otaa, msg='Publish Join Request %s, %s' % (
            Channel1.join_req_alarm, data))


class OTAAMsgDn:

    def __init__(self, dev_eui, app_eui, trans_params, ts=time.time()):
        self.dev_eui = dev_eui
        self.app_eui = app_eui
        self.trans_params = trans_params
        self.ts = int(ts)

    def __obj_to_dict(self):
        dd = {}
        # for key in self.fields:
        #     value = hexlify(getattr(self, key)).decode()
        #     dd[key] = value
        dd['trans_params'] = self.trans_params
        dd['ts'] = self.ts
        dd['dev_eui'] = hexlify(self.dev_eui).decode()
        return dd

    def publish(self):
        data = json.dumps(self.__obj_to_dict())
        # db1.publish(Channel1.join_req_alarm, data)
        db0.publish(Channel1.join_accept_alarm +
                    hexlify(self.app_eui).decode(), data)
        Logger.info(action=Action.otaa, msg='Publish Join Accept alram %s, %s' % (
            Channel1.join_req_alarm, data))


class JoinTransParams(TransParams):

    def save(self):
        pipe = db1.pipeline()
        key = ConstDB0.trans_params + \
            hexlify(self.dev_eui).decode() + ':' + \
            hexlify(self.gateway_mac_addr).decode()
        pipe.delete(key)
        pipe.hmset(key, self.trans_params)
        pipe.execute()

    # @classmethod
    # def move_to_db0(cls, dev_eui, gateway_mac_addr):
    #     db1.move(ConstDB0.trans_params + hexlify(dev_eui).decode() + ':' + hexlify(gateway_mac_addr).decode(), 0)

    class objects:

        @staticmethod
        def get(dev_eui, gateway_mac_addr, name=None):
            key = ConstDB0.trans_params + \
                hexlify(dev_eui).decode() + ':' + \
                hexlify(gateway_mac_addr).decode()
            if name is None:
                trans_params = db1.hgetall(key)
                return {key.decode(): value.decode() for key, value in trans_params.items()}
            else:
                trans_param = db1.hget(ConstDB0.trans_params + hexlify(
                    dev_eui).decode() + ':' + hexlify(gateway_mac_addr).decode(), name)
                return trans_param.decode() if trans_param else trans_param


class JoinDevGateway(DevGateway):
    # def add(self):
    # return db1.zadd(ConstDB0.dev_gateways + hexlify(self.dev_eui).decode(),
    # self.cal_score(), self.gateway_mac_addr)

    def add(self):
        score = self.cal_score()
        key = ConstDB0.dev_gateways + hexlify(self.dev_eui).decode()
        if not db1.execute_command('zadd', key, 'NX', score, self.gateway_mac_addr):
            Logger.debug(action='JoinDevGateway', type=IDType.device, id=self.dev_eui,
                         msg='zadd %s, %s already exists' % (key, hexlify(self.gateway_mac_addr).decode()))
            pre_score = db1.zscore(key, self.gateway_mac_addr)
            if score > pre_score:
                print()
                db1.zadd(key, score, self.gateway_mac_addr, nx=False)
                Logger.debug(action='JoinDevGateway', type=IDType.device, id=self.dev_eui, msg='zadd %s, %s refresh from %s to %s'
                             % (key, hexlify(self.gateway_mac_addr).decode(), pre_score, score))
                return True
            else:
                return False
        return True

    def set(self):
        pipe = db1.pipeline()
        pipe.zremrangebyrank(ConstDB0.dev_gateways +
                             hexlify(self.dev_eui).decode(), 0, -1)
        pipe.zadd(ConstDB0.dev_gateways + hexlify(self.dev_eui).decode(),
                  self.cal_score(), self.gateway_mac_addr)
        pipe.execute()

    # @classmethod
    # def move_to_db0(cls, dev_eui):
    #     db1.move(ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 0)

    @classmethod
    def set_best(cls, dev_eui, gateway_mac_addr):
        db1.zadd(ConstDB0.dev_gateways +
                 hexlify(dev_eui).decode(), 100, gateway_mac_addr)

    @classmethod
    def get_best_mac_addr(cls, dev_eui):
        key_list = db1.zrevrange(
            ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 0, 0)
        if len(key_list) > 0:
            return key_list[0]
        else:
            return None

    @classmethod
    def list_mac_addr_by_score(cls, dev_eui):
        key_list = db1.zrevrange(
            ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 0, -1)
        return key_list


class JoiningDev:

    def __init__(self, app_eui, dev_eui):
        # self.app_eui = app_eui
        self.app = Application.objects.get(app_eui)
        self.dev_eui = dev_eui

    class objects:

        @staticmethod
        def get(dev_eui):
            info = db1.hgetall(ConstDB0.dev + hexlify(dev_eui).decode())
            if info:
                join_dev = JoiningDev(
                    dev_eui=dev_eui, app_eui=info[b'app_eui'])
                return join_dev
