from binascii import hexlify
from utils.db0 import db0, ConstDB0
from utils.log import Logger, IDType
from utils.db2 import db2, ConstDB2
from .message import ConstMsg


class TransParams:
    def __init__(self, dev_eui, gateway_mac_addr, trans_params, ts):
        assert isinstance(dev_eui, bytes) and len(dev_eui) == 8, 'DevEUI ERROR'
        assert isinstance(gateway_mac_addr, bytes) and len(gateway_mac_addr) == 8, 'Gateway Mac Addr ERROR'
        assert isinstance(trans_params, dict), 'Trans_params ERROR'
        self.dev_eui = dev_eui
        self.gateway_mac_addr = gateway_mac_addr
        self.trans_params = trans_params
        self.ts = ts

    def save(self):
        hex_mac_addr = hexlify(self.gateway_mac_addr).decode()
        hex_dev_eui = hexlify(self.dev_eui).decode()
        pipe = db0.pipeline()
        key = ConstDB0.trans_params + hex_dev_eui + ':' + hex_mac_addr
        pipe.delete(key)
        pipe.hmset(key, self.trans_params)
        pipe.execute()

        pipe = db2.pipeline()
        key = ConstDB2.up_t + hex_dev_eui + ':' + hex_mac_addr + ':' + str(self.ts)
        pipe.rpush(ConstDB2.up_gateway + hex_mac_addr, self.ts)
        pipe.hmset(key, self.trans_params)
        s_key = ConstDB2.up_gw_s + hex_dev_eui + ':%s' % self.ts
        score = float(self.trans_params['rssi']) + float(self.trans_params['lsnr']) * 0.25
        pipe.zadd(s_key, score, hex_mac_addr)
        pipe.expire(key, ConstMsg.EXPIRE_STATIS)
        pipe.expire(s_key, ConstMsg.EXPIRE_STATIS)
        pipe.execute()

    class objects:
        @staticmethod
        def get(dev_eui, gateway_mac_addr, name=None):
            key = ConstDB0.trans_params + hexlify(dev_eui).decode() + ':' + hexlify(gateway_mac_addr).decode()
            if name is None:
                trans_params = db0.hgetall(key)
                return {key.decode(): value.decode() for key, value in trans_params.items()}
            else:
                trans_param = db0.hget(ConstDB0.trans_params + hexlify(dev_eui).decode() + ':' + hexlify(gateway_mac_addr).decode(), name)
                return trans_param.decode() if trans_param else trans_param


class DnTransParams:
    def __init__(self, category, eui, gateway_mac_addr, trans_params, ts):
        assert category == ConstDB0.dev or category == ConstDB0.group, 'DnTransParams category should be %s or %s, but %r got' % (ConstDB0.dev, ConstDB0.group, category)
        assert isinstance(eui, str), 'eui type should be str but %r got' % type(eui)
        self.category = category
        self.eui = eui.lower()
        self.gateway_mac_addr = gateway_mac_addr
        self.trans_params = trans_params
        self.ts = ts

    def save(self):
        hex_mac_addr = hexlify(self.gateway_mac_addr).decode()
        key = ConstDB2.dn_t + self.category + self.eui + ':' + hex_mac_addr + ':' + str(self.ts)
        db2.rpush(ConstDB2.dn_gateway + hex_mac_addr, self.ts)
        db2.hmset(key, self.trans_params)
        db2.expire(key, ConstMsg.EXPIRE_STATIS)


class DevGateway:
    def __init__(self, dev_eui, gateway_mac_addr, rssi, snr):
        assert isinstance(dev_eui, bytes) and len(dev_eui) == 8, 'DevEUI ERROR'
        assert isinstance(gateway_mac_addr, bytes) and len(gateway_mac_addr) == 8, 'Gateway Mac Addr ERROR'
        assert isinstance(rssi, int)
        assert isinstance(snr, float)
        self.dev_eui = dev_eui
        self.gateway_mac_addr = gateway_mac_addr
        self.rssi = rssi
        self.snr = snr

    def cal_score(self):
        return self.rssi + self.snr * 0.25

    def add(self):
        score = self.cal_score()
        key = ConstDB0.dev_gateways + hexlify(self.dev_eui).decode()
        if not db0.execute_command('zadd', key, 'NX', score, self.gateway_mac_addr):
            Logger.debug(action='DevGateway', type=IDType.device, id=self.dev_eui, msg='zadd %s, %s already exists' % (key, hexlify(self.gateway_mac_addr).decode()))
            pre_score = db0.zscore(key, self.gateway_mac_addr)
            if score > pre_score:
                print(type(score))
                db0.zadd(key, score, self.gateway_mac_addr)

                Logger.debug(action='DevGateway', type=IDType.device, id=self.dev_eui, msg='zadd %s, %s refresh from %s to %s'
                                                                                           % (key, hexlify(self.gateway_mac_addr).decode(), pre_score, score))
                return True
            else:
                return False
        return True

    def set(self):
        pipe = db0.pipeline()
        pipe.zremrangebyrank(ConstDB0.dev_gateways + hexlify(self.dev_eui).decode(), 0, -1)
        pipe.zadd(ConstDB0.dev_gateways + hexlify(self.dev_eui).decode(), self.cal_score(), self.gateway_mac_addr)
        pipe.execute()

    @classmethod
    def set_best(cls, dev_eui, gateway_mac_addr):
        db0.zadd(ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 100, gateway_mac_addr)

    @classmethod
    def get_best_mac_addr(cls, dev_eui):
        key_list = db0.zrevrange(ConstDB0.dev_gateways + hexlify(dev_eui).decode(), 0, 0)
        if len(key_list) > 0:
            return key_list[0]
        else:
            return None
