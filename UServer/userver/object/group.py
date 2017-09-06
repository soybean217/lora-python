from binascii import hexlify, unhexlify
from random import getrandbits

from userver.object.asserts import Assertions
from userver.frequency_plan import FrequencyPlan
from .const import FieldDevice, FieldGroup
from .que_down import QueDownGroup
from database.db0 import db0, ConstDB
from utils.errors import ReadOnlyDeny
from .addr import AddrManger
from userver.object.groupmysql import GroupDevice, Group as GroupMysql, Dev as DevMysql, DBSession, and_


class Group(object):
    fields = ('name', 'addr', 'nwkskey', 'appskey', 'fcnt', 'periodicity', 'datr')
    _vars_can_write = ('addr', 'name', 'nwkskey', 'appskey', 'fcnt', 'periodicity', 'datr')
    _assert_switcher = {'app_eui': Assertions.a_eui_64,
                         'addr': Assertions.a_dev_addr,
                         'name': Assertions.a_str,
                         'appskey': Assertions.a_appskey,
                         'nwkskey': Assertions.a_nwkskey,
                         'id': Assertions.a_eui_64,
                         'datr': Assertions.a_datarate,
                         'periodicity': Assertions.a_periodicity,
                         'fcnt': Assertions.a_fcnt}

    def __init__(self, app_eui, name, addr, nwkskey, appskey=b'', fcnt=0, periodicity=0, datr=0, id=None, new_flag=True):
        """
        :param app_eui: 8 bytes
        :param id: 8 bytes or None
        :param addr: 4 bytes
        :param appskey: b'' or 16 bytes
        :param nwkskey: 16 bytes
        """
        self.app_eui = app_eui
        self.name = name
        self.addr = addr
        self.appskey = appskey
        self.nwkskey = nwkskey
        self.fcnt = fcnt
        self.periodicity = periodicity
        self.datr = datr
        if new_flag is True:
            self.id = self.__dis_id()
        else:
            self.id = id
            self.que_down = QueDownGroup(self.app_eui, self.id)
            self.devices = self._get_device_list()
            self.freq_plan = self.__get_freq_plan()

    def __dis_id(self):
        i = 0
        while i < 256:
            id = self.__generate_id(bytes([i]))
            if not db0.exists(ConstDB.group+hexlify(id).decode()):
                return id
            i += 1

    @staticmethod
    def __generate_id(id_head):
        id = id_head
        for i in range(0, 7):
            id += bytes([getrandbits(8)])
        return id

    def __get_freq_plan(self):
        freq_plan = db0.hget(ConstDB.app + hexlify(self.app_eui).decode(), 'freq_plan')
        if freq_plan is not None:
            return FrequencyPlan(freq_plan.decode())

    def __zip_vars(self):
        if isinstance(self, Group):
            return {FieldGroup.app_eui: self.app_eui,
                    FieldGroup.name: self.name,
                    FieldGroup.addr: self.addr,
                    FieldGroup.nwkskey: self.nwkskey,
                    FieldGroup.appskey: self.appskey,
                    FieldGroup.fcnt: self.fcnt,
                    FieldGroup.periodicity: self.periodicity,
                    FieldGroup.datr: self.datr,
                    }
        else:
            return None

    def __zip_vars_can_write(self):
        if isinstance(self, Group):
            return {FieldGroup.name: self.name,
                    FieldGroup.addr: self.addr,
                    FieldGroup.nwkskey: self.nwkskey,
                    FieldGroup.appskey: self.appskey,
                    FieldGroup.fcnt: self.fcnt,
                    FieldGroup.periodicity: self.periodicity,
                    FieldGroup.datr: self.datr,
                    }
        else:
            return None

    def obj_to_dict(self):
        if isinstance(self, Group):
            return {FieldGroup.id: hexlify(self.id).decode().upper(),
                    FieldGroup.app_eui: hexlify(self.app_eui).decode().upper(),
                    FieldGroup.name: self.name,
                    FieldGroup.addr: hexlify(self.addr).decode().upper(),
                    FieldGroup.nwkskey: hexlify(self.nwkskey).decode().upper(),
                    FieldGroup.appskey: hexlify(self.appskey).decode().upper(),
                    FieldGroup.fcnt: self.fcnt,
                    FieldGroup.periodicity: self.periodicity,
                    FieldGroup.datr: self.datr,
                    'que_down': 0 if getattr(self, 'que_down', None) is None else self.que_down.len(),
                    'freq_plan': getattr(self, 'freq_plan', self.__get_freq_plan()).value,
                    # 'que_down': self.que_down.len()
                    }
        else:
            return None

    def __setattr__(self, key, value):
        try:
            attr = getattr(self, key)
            if attr is not None and key not in self._vars_can_write:
                raise ReadOnlyDeny
        except AttributeError:
            pass
        if key in self._assert_switcher:
            self._assert_switcher[key](value)
        self.__dict__[key] = value

    def _get_device_list(self):
        """
         keys = db0.keys(ConstDB.group_dev + hexlify(self.id).decode() + ':*')
        return [unhexlify(key.decode().split(':')[2]) for key in keys]
        """
        group_id = hexlify(self.id).decode()
        dbsession = DBSession()
        query = dbsession.query(GroupDevice.dev_id).filter(GroupDevice.group_id == group_id).all()
        dbsession.close()
        return [i_query[0] for i_query in query]

    def save(self):
        group_key = ConstDB.group + hexlify(self.id).decode()
        AddrManger.addr_available(self.addr)
        pipe = db0.pipeline()
        pipe.sadd(ConstDB.app_groups + hexlify(self.app_eui).decode(), self.id)
        pipe.hmset(group_key, self.__zip_vars())
        pipe.set(ConstDB.addr + hexlify(self.addr).decode(), group_key)
        pipe.execute()
        
    def update(self):
        pipe = db0.pipeline()
        group_key = ConstDB.group + hexlify(self.id).decode()
        orignal_addr = db0.hget(group_key, FieldGroup.addr)
        if self.addr != orignal_addr:
            AddrManger.addr_available(self.addr)
            pipe.rename(ConstDB.addr + hexlify(orignal_addr).decode(), ConstDB.addr + hexlify(self.addr).decode())
        pipe.hmset(group_key, self.__zip_vars_can_write())
        pipe.execute()

    def delete(self):
        group_id_hex = hexlify(self.id).decode()
        group_key = ConstDB.group + group_id_hex
        """
        group_devs = db0.keys(ConstDB.group_dev + group_id_hex + ':*')
        """
        group_devs_list = self._get_device_list()
        group_devs = [(ConstDB.group_dev + group_id_hex + ':' + i_group_list).encode() for i_group_list in group_devs_list]
        statistics_down = db0.keys(ConstDB.statistics_down + group_key + ':*')
        msg_down = db0.keys(ConstDB.msg_down + group_key + ':*')
        pipe = db0.pipeline()
        for key in group_devs:
            pipe.delete(key)
        for key in msg_down:
            pipe.delete(key)
        for key in statistics_down:
            pipe.delete(key)
        pipe.srem(ConstDB.app_groups + hexlify(self.app_eui).decode(), self.id)
        pipe.delete(ConstDB.que_down + group_key)
        pipe.delete(ConstDB.addr + hexlify(self.addr).decode())
        pipe.delete(group_key)
        pipe.execute()
        AddrManger.recycle_addr(self.addr)

    def add_device(self, dev_eui):
        """
        :param dev_eui: bytes
        :return:
        """
        dev_eui = hexlify(dev_eui).decode()
        dev_app_eui = db0.hget(ConstDB.dev + dev_eui, FieldDevice.app_eui)
        if self.app_eui == dev_app_eui:
            """
            db0.set(ConstDB.group_dev + hexlify(self.id).decode() + ':' + dev_eui, 1)
            """
            dbsession = DBSession()
            group_id = hexlify(self.id).decode()
            query = dbsession.query(GroupMysql).filter(GroupMysql.id == group_id)
            if query.count() == 0:
                group_init = GroupMysql(id=group_id)
                dbsession.add(group_init)
            else:
                group_init = query.first()
            query = dbsession.query(DevMysql).filter(DevMysql.id == dev_eui)
            if query.count() == 0:
                dev_init = DevMysql(id=dev_eui)
                dbsession.add(dev_init)
            else:
                dev_init = query.first()
            query = dbsession.query(GroupDevice).filter(and_(GroupDevice.group_id == group_id,
                                                             GroupDevice.dev_id == dev_eui)
                                                        ).count()
            if query == 0:
                group_init.devs.append(dev_init)
                dbsession.commit()
            dbsession.close()
        else:
            raise KeyError('No such Device in this Application')

    def rem_device(self, dev_eui):
        """
        dev_eui = hexlify(dev_eui).decode()
        return db0.delete(ConstDB.group_dev + hexlify(self.id).decode() + ':' + dev_eui)
        :param dev_eui: bytes
        :return:
        """
        dev_eui = hexlify(dev_eui).decode()
        dbsession = DBSession()
        group_id = hexlify(self.id).decode()
        dev_id = dev_eui

        query = dbsession.query(GroupDevice).filter(and_(GroupDevice.dev_id == dev_id,
                                                         GroupDevice.group_id == group_id))
        if query.count() != 0:
            for i_query in query.all():
                dbsession.delete(i_query)
        dbsession.commit()
        dbsession.close()

    class objects:
        @staticmethod
        def get(id):
            """
            :param app_eui: 8 bytes
            :param id: bytes
            :return:
            """
            info = db0.hgetall(ConstDB.group + hexlify(id).decode())
            if len(info) > 0:
                app_eui = info[b'app_eui']
                name = info[b'name'].decode()
                addr = info[b'addr']
                nwkskey = info[b'nwkskey']
                appskey = info.get(b'appskey')
                fcnt = int(info[b'fcnt'])
                periodicity = int(info.get(b'periodicity', 0))
                datr = int(info.get(b'datr', 0))
                return Group(app_eui, name, addr, nwkskey, appskey, fcnt, periodicity=periodicity, datr=datr, id=id, new_flag=False)

        @classmethod
        def all(cls, app_eui=None):
            """
            :param app_eui: 8 bytes
            :return:
            """
            groups = []
            if app_eui is not None:
                keys = db0.smembers(ConstDB.app_groups + hexlify(app_eui).decode())
                for key in keys:
                    group = cls.get(key)
                    groups.append(group)
            else:
                keys = db0.keys(ConstDB.group + '*')
                for key in keys:
                    group = cls.get(unhexlify(key.decode().split(':')[1]))
                    groups.append(group)
            return groups

        @classmethod
        def all_eui(cls, app_eui):
            """
            :param app_eui: 8 bytes
            :return: str
            """
            keys = db0.smembers(ConstDB.app_groups + hexlify(app_eui).decode())
            return keys

        @classmethod
        def all_dict(cls, app_eui):
            keys = db0.smembers(ConstDB.app_groups + hexlify(app_eui).decode())
            groups = []
            for key in keys:
                group = cls.get(key)
                groups.append(group.obj_to_dict())
            return groups

        # @classmethod
        # def all_json(cls, app_eui):
        #     keys = db0.keys(ConstDB.group + hexlify(app_eui).decode() + ':*')
        #     groups = []
        #     for key in keys:
        #         id = unhexlify(key.decode().split(':')[2])
        #         group = cls.get(app_eui, id)
        #         group_dict = {key: hexlify(val).decode() if(type(val) == bytes)else val for key, val in group._obj_to_dict().items()}
        #         group_dict['group_id'] = hexlify(id).decode()
        #         group_dict['app_eui'] = hexlify(app_eui).decode()
        #         groups.append(group_dict)
        #     return json.dumps(groups)

        # @staticmethod
        # def get_json(app_eui, id, group=None):
        #     if group is None:
        #         group = Group.objects.get(app_eui, id)
        #     if group is not None:
        #         group_dict = {key: hexlify(val).decode() if(type(val) == bytes)else val for key, val in group._obj_to_dict().items()}
        #         group_dict['group_id'] = hexlify(id).decode()
        #         return json.dumps(group_dict)
        #     else:
        #         return json.dumps("Application: %s do not have group: %s" % (hexlify(app_eui).decode(), hexlify(id).decode()))

        ##?
    # def patch(self, form):
    #     for key in form:
    #         if key == 'rm_appskey':
    #             if form[key] == 'True':
    #                 self.appskey = b''
    #             elif form[key] != 'False':
    #                 raise AssertionError('%s must be True or false' % key)
    #         elif key == 'appskey':
    #             if len(form[key]) != 32:
    #                 raise AssertionError('%s must be 32 hex'%key)
    #             else:
    #                 self.appskey = unhexlify(form[key])
    #         elif key == 'nwkskey':
    #             if len(form[key]) != 32:
    #                 raise AssertionError('%s must be 32 hex'%key)
    #             else:
    #                 self.appskey = unhexlify(form[key])
    #         elif key == 'reset_fcnt_up':
    #             if form[key] == 'True':
    #                 self.fcnt = 0
    #             elif form[key] != 'False':
    #                 raise AssertionError('%s must be True or false' % key)
    #         elif key == 'reset_fcnt_down':
    #             if form[key] =='True':
    #                 self.que_down.clear()
    #             elif form[key] != 'False':
    #                 raise AssertionError('%s must be True or false' % key)
    #         elif key == 'datr':
    #             datr = int(form[key])
    #             if 0 <= datr < 7:
    #                 self.datr = datr
    #             else:
    #                 raise AssertionError('%s must from 0 to 6' % key)
    #         elif key == 'addr':
    #             if len(form[key]) != 8:
    #                 raise AssertionError('%s must be 8 hex' % key)
    #             else:
    #                 self.addr = unhexlify(form[key])
    #         elif key == 'periodicity':
    #             periodicity = int(form[key])
    #             if 0 <= periodicity <= 6:
    #                 self.periodicity = periodicity
    #             else:
    #                 raise AssertionError('%s must from 0 to 6' % key)
    #         elif key == 'name':
    #             self.name = form[key]
    #         elif key == 'add_dev':
    #             if len(form[key]) != 16:
    #                 raise AssertionError('%s must be 16 hex'% key)
    #             else:
    #                 self.add_device(unhexlify(form[key]))
    #         elif key =='rm_dev':
    #             if len(form[key]) != 16:
    #                 raise AssertionError('%s must be 16 hex'% key)
    #             else:
    #                 self.rem_device(unhexlify(form[key]))
    #     self.update()
    #     return

