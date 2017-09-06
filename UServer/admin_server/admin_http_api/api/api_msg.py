import json
from binascii import hexlify

from flask import Response, request

from userver.object.device import Device
from userver.object.group import Group
from .decorators import msg_filter_valid
from userver.object.application import Application
from ..http_auth import auth
from userver.object.message import MsgUp, MsgDn
from . import api, root


@api.route(root+'msg-up', methods=['GET'])
@auth.auth_required
@msg_filter_valid
def msg_up(user=None, app=None, device=None, group=None, start_ts=0, end_ts=-1):
    if request.method == 'GET':
        if group is not None:
            return 'Group has no msg up', 406
        if device is not None:
            msgs = MsgUp.objects.all(device.app_eui, device.dev_eui, start_ts=start_ts, end_ts=end_ts, cur_cnt=500)
            msg_up_json = json.dumps([msg.obj_to_dict() for msg in msgs])
        elif app is not None:
            msgs = MsgUp.objects.all(app.app_eui, start_ts=start_ts, end_ts=end_ts, cur_cnt=500)
            msg_up_json = json.dumps([msg.obj_to_dict() for msg in msgs])
        else:
            if user is not None:
                apps = Application.query.filter_by(user_id=user.id)
            else:
                apps = Application.query.order_by(Application.user_id)
            msg_all = []
            for app in apps:
                msgs = MsgUp.objects.all(app.app_eui, start_ts=start_ts, end_ts=end_ts, cur_cnt=500)
                msg_all.append({'app': hexlify(app.app_eui).decode(), 'msg_up': [msg.obj_to_dict() for msg in msgs]})
            msg_up_json = json.dumps(msg_all)
        return Response(status=200, response=msg_up_json)


@api.route(root+'msg-down', methods=['GET'])
@auth.auth_required
@msg_filter_valid
def msg_down(user=None, app=None, group=None, device=None, start_ts=0, end_ts=-1):
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
                                 'message_down': msg_list})
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