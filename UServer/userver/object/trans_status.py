from binascii import hexlify, unhexlify
from database.db0 import db0, ConstDB


class TransStatus(object):
    fields = ('time', 'datr', 'rssi', 'lsnr', 'freq')

    def __init__(self, dev_eui, gateway_id, info):
        """
        :param dev_eui:
        :param gateway_id:
        :param trans_params:
        :return:
        """
        assert isinstance(dev_eui, bytes) and len(dev_eui) == 8, 'DevEUI ERROR'
        assert isinstance(gateway_id, bytes) and len(gateway_id) == 8, 'Gateway ID ERROR'
        self.dev_eui = dev_eui
        self.gateway_id = gateway_id
        for key, value in info.items():
            setattr(self, key, value)

    def obj_to_dict(self):
        info = {}
        for key, value in self.__dict__.items():
            if isinstance(value, str):
                info[key] = value
            elif isinstance(value, bytes):
                info[key] = hexlify(value).decode()
        return info

    class objects:
        @classmethod
        def all(cls, dev_eui=None, gateway_id=None):
            """
            :param dev_eui: bytes
            :return:
            """
            list_trans_params = []
            if dev_eui is not None:
                keys = db0.keys(pattern=ConstDB.trans_params + hexlify(dev_eui).decode() + ':*')
                for key in keys:
                    trans_params = cls.get(dev_eui, unhexlify(key.decode().split(':')[2]))
                    list_trans_params.append(trans_params)
            elif gateway_id is not None:
                keys = db0.keys(pattern=ConstDB.trans_params + '*:' + hexlify(gateway_id).decode())
                for key in keys:
                    trans_params = cls.get(unhexlify(key.decode().split(':')[1]), gateway_id)
                    list_trans_params.append(trans_params)
            return list_trans_params

        @classmethod
        def all_dict(cls, dev_eui=None, gateway_id=None):
            """
            :param dev_eui: bytes
            :return:
            """
            list_trans_params = []
            if dev_eui is not None:
                keys = db0.keys(pattern=ConstDB.trans_params + hexlify(dev_eui).decode() + ':*')
                for key in keys:
                    trans_params = cls.get(dev_eui, unhexlify(key.decode().split(':')[2])).obj_to_dict()
                    list_trans_params.append(trans_params)
            elif gateway_id is not None:
                keys = db0.keys(pattern=ConstDB.trans_params + '*:' + hexlify(gateway_id).decode())
                for key in keys:
                    trans_params = cls.get(unhexlify(key.decode().split(':')[1]), gateway_id).obj_to_dict()
                    list_trans_params.append(trans_params)
            return list_trans_params

        @classmethod
        def best(cls, dev_eui):
            """
            :param dev_eui:
            :return:
            """
            best_gateway_id = db0.zrevrange(ConstDB.dev_gateways + hexlify(dev_eui).decode(), 0, 1)
            if len(best_gateway_id) > 0:
                return cls.get(dev_eui, best_gateway_id[0])
            else:
                return None

        @staticmethod
        def get(dev_eui, gateway_id):
            """
            :param dev_eui: bytes
            :param gateway_id: bytes
            :return: TransParams
            """
            info = db0.hgetall(ConstDB.trans_params + hexlify(dev_eui).decode() + ':' + hexlify(gateway_id).decode())
            info = {key.decode(): value.decode() for key, value in info.items()}
            return TransStatus(dev_eui, gateway_id, info)