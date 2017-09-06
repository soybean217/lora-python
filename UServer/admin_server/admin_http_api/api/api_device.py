from flask import request
from binascii import unhexlify, hexlify
import json
from userver.object.application import Application
from userver.object.device import Device
from userver.object.statistician import Statistician, ConstStatis
from . import api, root
from ..http_auth import auth
from .decorators import device_exists, device_filter_valid

@api.route(root + 'devices/<dev_eui>/statistician/daily', methods=['GET', 'POST'])
@auth.auth_required
@device_exists
def device_statistician_daily(device):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    statistician = Statistician(hexlify(device.dev_eui).decode(), ConstStatis.dev)
    msg_up_daily = statistician.msg_up_count_in_daily()
    msg_down_daily = statistician.msg_down_count_in_daily()
    msg_retrans_daily = statistician.msg_retrans_count_in_daily()
    return json.dumps([{'name': 'uplink', 'data': msg_up_daily}, {'name': 'retrans', 'data': msg_retrans_daily}, {'name': 'downlink', 'data': msg_down_daily}]), 200


@api.route(root + 'devices/<dev_eui>/statistician/hourly', methods=['GET', 'POST'])
@auth.auth_required
@device_exists
def device_statistician_hourly(device):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    statistician = Statistician(hexlify(device.dev_eui).decode(), ConstStatis.dev)
    msg_up = statistician.msg_up_count_in_hour()
    msg_down = statistician.msg_down_count_in_hour()
    msg_retrans = statistician.msg_retrans_count_in_hour()
    return json.dumps([{'name': 'uplink', 'data': msg_up}, {'name': 'retrans', 'data': msg_retrans}, {'name': 'downlink', 'data': msg_down}]), 200


@api.route(root + 'devices', methods=['GET', 'PATCH', 'DELETE', 'POST'])
@auth.auth_required
@device_filter_valid
def devices(user=None, app=None, group=None, *args, **kwargs):
    if request.method == 'GET':
        if group is not None:
            devices = Device.objects.all(group_id=group.id)
        elif app is not None:
            _group = request.args.get('!group')
            if _group is not None:
                group_devices = Device.objects.all(group_id=unhexlify(_group))
                devices = set(app.devices) - set(group_devices)
            else:
                devices = app.devices
        elif user is not None:
            devices = Device.query.join(Application, Device.app_eui==Application.app_eui).filter(Application.user_id==user.id).order_by(Device.app_eui)
        else:
            devices = Device.query.order_by(Device.app_eui)
        devices = [device.obj_to_dict() for device in devices]
        devices_json = json.dumps(devices)
        return devices_json, 200


@api.route(root + 'devices/<dev_eui>', methods=['GET', 'PATCH', 'DELETE', 'POST'])
@auth.auth_required
@device_exists
def device(device):
    if request.method == 'GET':
        return json.dumps(device.obj_to_dict()), 200