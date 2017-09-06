from utils.db0 import db0, ConstDB0
from utils.exception import ReadOnlyDeny
from binascii import hexlify, unhexlify
from object.que_down import QueDownGroup
from object.application import Application
from object.asserts import Assertions
from object.groupmysql import DBSession, GroupDevice


class FieldGroup:
    app_eui = 'app_eui'
    nwkskey = 'nwkskey'
    appskey = 'appskey'
    addr = 'addr'
    fcnt = 'fcnt'
    periodicity = 'periodicity'
    datarate = 'datarate'
    frequency = 'frequency'
    que_down = 'que_down'
    id = 'id'


class Group(object):
    fields = (FieldGroup.app_eui, FieldGroup.addr, FieldGroup.app_eui,
              FieldGroup.nwkskey, FieldGroup.appskey, FieldGroup.fcnt,)
    __vars_can_write = (FieldGroup.fcnt, )
    __assert_switcher = {
                         # FieldGroup.app_eui: Assertions.a_eui,
                         'app': Application.assert_isinstanceof,
                         FieldGroup.id: Assertions.a_bytes,
                         FieldGroup.addr: Assertions.a_addr,
                         FieldGroup.nwkskey: Assertions.a_nwkskey,
                         FieldGroup.appskey: Assertions.a_appskey,
                         FieldGroup.fcnt: Assertions.a_fcnt,
                         FieldGroup.periodicity: Assertions.a_periodicity,
                         FieldGroup.datarate: Assertions.a_pass,
                         FieldGroup.que_down: QueDownGroup.assert_isinstanceof,
                         'devices': Assertions.a_list,
                         }

    def __init__(self, app_eui, id, addr, nwkskey, appskey, fcnt, periodicity, datarate):
        """
        :param app_eui: 8 bytes
        :param id: bytes
        :param addr: 4 bytes
        :param nwkskey: 8 bytes
        :param appskey: 8 bytes or b''
        :param fcnt: isinstance(fcnt, int) and 0 <= fcnt < 0x100000000
        :param periodicity: 0-7
        :param datarate: number
        :return:
        """
        # self.app_eui = app_eui
        self.app = Application.objects.get(app_eui)
        self.id = id
        self.addr = addr
        self.appskey = appskey
        self.nwkskey = nwkskey
        self.fcnt = fcnt
        self.periodicity = periodicity
        self.datarate = datarate
        self.devices = self._get_device_list()
        try:
            self.que_down = QueDownGroup(self.app.app_eui, self.id)
        except Exception as error:
            raise error

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in self.__vars_can_write:
                raise ReadOnlyDeny
        self.__assert_switcher[key](value)
        self.__dict__[key] = value

    def update(self):
        m_dict = {}
        for field in self.__vars_can_write:
            m_dict[field] = self.__dict__[field]
        group_key = ConstDB0.group + hexlify(self.id).decode()
        db0.hmset(group_key, m_dict)

    def _get_device_list(self):
        '''
        keys = db0.keys(ConstDB0.group_dev + hexlify(self.id).decode() + ':*')
        return [unhexlify(key.decode().split(':')[2]) for key in keys]
        '''
        group_id = hexlify(self.id).decode()
        dbsession = DBSession()
        query = dbsession.query(GroupDevice.dev_id).filter(GroupDevice.group_id == group_id).all()
        dbsession.close()
        return [unhexlify(i_query[0]) for i_query in query]

    class objects:
        @staticmethod
        def get(id):
            """
            :param id: 8 bytes
            :return:
            """
            info = db0.hgetall(ConstDB0.group + hexlify(id).decode())
            if len(info) > 0:
                app_eui = info[b'app_eui']
                addr = info[b'addr']
                nwkskey = info[b'nwkskey']
                appskey = info.get(b'appskey')
                fcnt = int(info[b'fcnt'])
                periodicity = int(info.get(b'periodicity', 0))
                datarate = int(info.get(b'datarate', 0))
                return Group(app_eui, id, addr, nwkskey, appskey, fcnt, periodicity, datarate)

