import json
import cgi
from binascii import hexlify

from flask import Response, request
from .decorators import msg_filter_valid, require_basic_or_oauth
from userver.object.application import Application
from userver.object.message import MsgUp, MsgDn
from . import api, root
import time
from database.db0 import db0,ConstDB


class DataTablesServer:
    column = ('ts', 'fcnt', 'port', 'freq', 'datr', 'rssi', 'lsnr', 'data', 'cipher')

    def __init__(self, request, device):
        self.args = request.args
        self.dev_eui = hexlify(device.dev_eui).decode()
        self.app_eui = hexlify(device.app.app_eui).decode()
        self.order_by = self.args['order[0][column]']
        self.order_by = self.args['columns[' + self.order_by + '][data]']
        self.length = int(self.args['length'])
        self.draw = int(self.args['draw'])
        self.start = int(self.args['start'])
        self.desc = (self.args['order[0][dir]'] == 'desc')

    def check(self):
        list = db0.sort(ConstDB.mset + self.dev_eui)
        i = 0
        for ts in list:
            info = db0.hgetall(ConstDB.msg_up + self.app_eui + ':' + self.dev_eui + ':' + ts.decode())
            if len(info) == 0:
                db0.srem(ConstDB.mset + self.dev_eui, ts)
                i += 1
            else:
                print('%s messages deleted' % i)
                return

    def query(self):
        if self.order_by in ('fcnt', 'port', 'freq', 'rssi', 'lsnr'):
            list = db0.sort(ConstDB.mset + self.dev_eui, by=ConstDB.msg_up + self.app_eui + ':' + self.dev_eui + ':*->' + self.order_by, desc=self.desc)
        elif self.order_by in ('datr', 'data'):
            list = db0.sort(ConstDB.mset + self.dev_eui, by=ConstDB.msg_up + self.app_eui + ':' + self.dev_eui + ':*->' + self.order_by, alpha=True, desc=self.desc)
        else:
            list = db0.sort(ConstDB.mset + self.dev_eui, desc=self.desc)
        msg_list = []
        index = self.start
        while len(msg_list) < self.length:
            try:
                ts = int(list[index])
            except IndexError:
                break
            info = db0.hgetall(ConstDB.msg_up + self.app_eui + ':' + self.dev_eui + ':' + str(ts))
            if len(info) > 0:
                msg = {'ts': ts}
                for key, value in info.items():
                    key = key.decode()
                    if key == 'data':
                        msg[key] = hexlify(value).decode()
                    elif key in ['fcnt', 'port']:
                        msg[key] = int(value)
                    elif key in ['freq', 'rssi', 'lsnr']:
                        msg[key] = float(value)
                    else:
                        msg[key] = value.decode()
                msg_list.append(msg)
                index += 1
            else:
                db0.srem(ConstDB.mset + self.dev_eui, ts)
                del list[index]
        return {"draw": self.draw, "recordsTotal": len(list), "recordsFiltered": len(list), "data": msg_list}


@api.route(root+'datatables/msg-up', methods=['GET'])
@require_basic_or_oauth
@msg_filter_valid
def dt_msg_up(user, app=None, device=None, group=None, start_ts=0, end_ts=-1, max=0):
    if request.method == 'GET':
        dt = DataTablesServer(request, device)
        dt.check()
        return json.dumps(dt.query()), 200