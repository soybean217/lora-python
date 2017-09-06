import json
from binascii import hexlify

from flask import Response, request

from userver.object.device import Device
from userver.object.group import Group
from .decorators import msg_filter_valid, require_basic_or_oauth
from userver.object.application import Application
from userver.object.message import MsgUp, MsgDn
from . import api, root
import time


@api.route(root+'msg-up', methods=['GET'])
@require_basic_or_oauth
@msg_filter_valid
def msg_up(user, app=None, device=None, group=None, start_ts=0, end_ts=-1, max=0):
    if request.method == 'GET':
        time0 = time.time()
        if group is not None:
            return Response(status=404, response=json.dumps('Group has no message up.'))
        elif device is not None:
            msgs = MsgUp.objects.all(device.app_eui, device.dev_eui, start_ts=start_ts, end_ts=end_ts, cur_cnt=max)
            time1 = time.time()
            msgs = [msg.obj_to_dict() for msg in msgs]
        elif app is not None:
            msgs = MsgUp.objects.all(app.app_eui, start_ts=start_ts, end_ts=end_ts, cur_cnt=max)
            time1 = time.time()
            msgs = [msg.obj_to_dict() for msg in msgs]
        else:
            apps = Application.query.filter_by(user_id=user.id)
            time1 = time.time()
            msgs = []
            for app in apps:
                msgs_app = MsgUp.objects.all(app.app_eui, start_ts=start_ts, end_ts=end_ts, cur_cnt=max)
                msgs.append({'app': hexlify(app.app_eui).decode(), 'msg-up': [msg.obj_to_dict() for msg in msgs_app]})
        time2 = time.time()
        msg_up_json = json.dumps(msgs)
        time3 = time.time()
        return Response(status=200, response=msg_up_json)


@api.route(root+'msg-down', methods=['GET'])
@require_basic_or_oauth
@msg_filter_valid
def msg_down(user, app=None, group=None, device=None, start_ts=0, end_ts=-1):
    if request.method == 'GET':
        if device is None and group is None and app is not None:
            msg_list = []
            devices = Device.objects.all(app.app_eui)
            groups = Group.objects.all(app.app_eui)
            for device in devices:
                msgs = MsgDn.objects.all(type='DEV', eui=device.dev_eui, start_ts=start_ts, end_ts=end_ts)
                for msg in msgs:
                    msg_list.append(msg.obj_to_dict())
            for group in groups:
                msgs = MsgDn.objects.all(type='GROUP', eui=group.id, start_ts=start_ts, end_ts=end_ts)
                for msg in msgs:
                    msg_list.append(msg.obj_to_dict())
            return Response(status=200, response=json.dumps(msg_list))
        elif app is None and group is None and device is None:
            apps = Application.query.filter_by(user_id=user.id)
            app_list = []
            for app in apps:
                msg_list = []
                devices = Device.objects.all(app.app_eui)
                groups = Group.objects.all(app.app_eui)
                for device in devices:
                    msgs = MsgDn.objects.all(type='DEV', eui=device.dev_eui, start_ts=start_ts, end_ts=end_ts)
                    for msg in msgs:
                        msg_list.append(msg.obj_to_dict())
                for group in groups:
                    msgs = MsgDn.objects.all(type='GROUP', eui=group.id, start_ts=start_ts, end_ts=end_ts)
                    for msg in msgs:
                        msg_list.append(msg.obj_to_dict())
                app_list.append({'app': hexlify(app.app_eui).decode(),
                                 'msg-down': msg_list})
            return Response(status=200, response=json.dumps(app_list))
        else:
            msg_list = []
            if device is not None:
                msgs = MsgDn.objects.all(type='DEV', eui=device.dev_eui, start_ts=start_ts, end_ts=end_ts)
                for msg in msgs:
                    msg_list.append(msg.obj_to_dict())
            if group is not None:
                msgs = MsgDn.objects.all(type='GROUP', eui=group.id, start_ts=start_ts, end_ts=end_ts)
                for msg in msgs:
                    msg_list.append(msg.obj_to_dict())
            return Response(status=200, response=json.dumps(msg_list))