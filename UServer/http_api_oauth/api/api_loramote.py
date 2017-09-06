from binascii import hexlify
import json
from flask import request
from .decorators import require_basic_or_oauth, loramote_filter_valid, device_belong_to_user
from userver.object.loramote import LoRaMote
from . import api, loramote


@api.route(loramote + '/<dev_eui>/rssi', methods=['GET'])
@require_basic_or_oauth
@device_belong_to_user
@loramote_filter_valid
def loramote_rssi(user, app, device, gateway=None, start_ts=0, end_ts=-1):
    loramote = LoRaMote(device.dev_eui)
    rssi = loramote.stat_rssi_snr(gateway.id, start_ts=start_ts, end_ts=end_ts) if gateway else loramote.stat_rssi_snr(start_ts=start_ts, end_ts=end_ts)
    return json.dumps(rssi), 200


@api.route(loramote + '/<dev_eui>/uplinks', methods=['GET'])
@require_basic_or_oauth
@device_belong_to_user
@loramote_filter_valid
def loramote_uplinks(user, app, device, gateway=None, start_ts=0, end_ts=-1):
    loramote = LoRaMote(device.dev_eui)
    uplinks = loramote.uplinks(g_id=hexlify(gateway.id).decode() if gateway else None, start_ts=start_ts, end_ts=end_ts)
    return json.dumps(uplinks), 200


@api.route(loramote + '/<dev_eui>/retrans', methods=['GET'])
@require_basic_or_oauth
@device_belong_to_user
@loramote_filter_valid
def loramote_retrans(user, app, device, gateway=None, start_ts=0, end_ts=-1):
    loramote = LoRaMote(device.dev_eui)
    uplinks = loramote.stat_retrans(start_ts=start_ts, end_ts=end_ts)
    return json.dumps(uplinks), 200


@api.route(loramote + '/<dev_eui>/retrans_dist', methods=['GET'])
@require_basic_or_oauth
@device_belong_to_user
@loramote_filter_valid
def loramote_retrans_dist(user, app, device, gateway=None, start_ts=0, end_ts=-1):
    loramote = LoRaMote(device.dev_eui)
    uplinks = loramote.stat_retrans_dist(g_id=gateway.id if gateway else None, start_ts=start_ts, end_ts=end_ts)
    return json.dumps(uplinks), 200