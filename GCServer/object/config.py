import json
from jsmin import jsmin
from object.frequency_plan import FrequencyPlan


class Fields:
    sftp_conf = 'sftp_conf'


class Config:

    __map_FreqPlan_ConfigFileName = {
        FrequencyPlan.EU863_870: 'EU863_870_conf',
        FrequencyPlan.EU433: 'EU433_conf',
        FrequencyPlan.CN470_510: 'CN470_510_conf',
        FrequencyPlan.MT433: 'MT433_conf',
        FrequencyPlan.CP500: 'CP500_conf',
        FrequencyPlan.CNICG470: 'CNICG470_conf',
        Fields.sftp_conf: 'sftp_conf'
    }

    @staticmethod
    def read_conf_file(file_name):
        file_conf = open("configs/" + file_name + ".json", 'r')
        __config = json.loads(jsmin(file_conf.read()))
        file_conf.close()
        return __config

    """
    file_EU863_870_conf = open("configs/EU863_870_conf.json", 'r')
    file_EU433_conf = open("configs/EU433_conf.json", 'r')
    file_CN470_510_conf = open("configs/CN470_510_conf.json", 'r')
    file_MT433_conf = open("configs/MT433_conf.json", "r")
    file_CP500_conf = open("configs/CP500_conf.json", "r")
    file_CNICG470_conf = open("configs/CNICG470_conf.json", "r")
    file_sftp_conf = open("configs/sftp_conf.json", 'r')

    __EU863_870 = json.loads(jsmin(file_EU863_870_conf.read()))
    __EU433 = json.loads(jsmin(file_EU433_conf.read()))
    __CN470_510 = json.loads(jsmin(file_CN470_510_conf.read()))
    __MT433 = json.loads(jsmin(file_MT433_conf.read()))
    __CP500 = json.loads(jsmin(file_CP500_conf.read()))
    __CNICG470 = json.loads(jsmin(file_CNICG470_conf.read()))
    __sftp_conf = json.loads(jsmin(file_sftp_conf.read()))

    file_EU863_870_conf.close()
    file_EU433_conf.close()
    file_CN470_510_conf.close()
    file_MT433_conf.close()
    file_CP500_conf.close()
    file_CNICG470_conf.close()
    file_sftp_conf.close()
    """

    # def __setattr__(self, key, value):
    #     if hasattr(self, key):
    #         raise PermissionError("Can't rebind const instance attribute (%s)" % key)
    #     self.__dict__[key] = value

    # def __delattr__(self, key):
    #     if self.__dict__.has_key(key):
    #         raise PermissionError("Can't unbind const const instance attribute (%s)" % key)
    #     raise AttributeError("const instance has no attribute '%s'" % key)

    @classmethod
    def get_conf(cls, file_type, protocol_version):
        """
        if file_type == FrequencyPlan.EU433:
            return dict(cls.__EU433)
        elif file_type == FrequencyPlan.EU863_870:
            return dict(cls.__EU863_870)
        elif file_type == FrequencyPlan.CN470_510:
            return dict(cls.__CN470_510)
        elif file_type == FrequencyPlan.MT433:
            return dict(cls.__MT433)
        elif file_type == FrequencyPlan.CP500:
            return dict(cls.__CP500)
        elif file_type == FrequencyPlan.CNICG470:
            return dict(cls.__CNICG470)
        elif file_type == 'update':
            return dict(cls.__sftp_conf)
        """
        suffix = ''
        file_name = cls.__map_FreqPlan_ConfigFileName.get(file_type, '')
        if file_type == FrequencyPlan.EU433:
            pass
        elif file_type == FrequencyPlan.EU863_870:
            pass
        elif file_type == FrequencyPlan.CN470_510:
            suffix = '_' + str(protocol_version)
        elif file_type == FrequencyPlan.MT433:
            pass
        elif file_type == FrequencyPlan.CP500:
            pass
        elif file_type == FrequencyPlan.CNICG470:
            pass
        elif file_type == 'update':
            file_name = cls.__map_FreqPlan_ConfigFileName.get(Fields.sftp_conf, '')
        if file_name:
            contain = cls.read_conf_file(file_name + suffix)
            return dict(contain)
