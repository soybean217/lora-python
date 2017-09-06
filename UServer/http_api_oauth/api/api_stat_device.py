import json
from flask import request
from .decorators import require_basic_or_oauth, device_belong_to_user
from userver.object.stat_device import Statistician
from . import api, stat


@api.route(stat + '/devices/<dev_eui>/uplinks', methods=['GET'])
@require_basic_or_oauth
@device_belong_to_user
def stat_device_uplinks(user, app, device):
    if request.method == 'GET':
        info = Statistician.count_uplink(device.dev_eui)
        return json.dumps(info), 200


@api.route(stat + '/devices/<dev_eui>/retrans', methods=['GET'])
@require_basic_or_oauth
@device_belong_to_user
def stat_device_retrans(user, app, device):
    if request.method == 'GET':
        info = Statistician.count_retrans(device.dev_eui)
        return json.dumps(info), 200