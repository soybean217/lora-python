from binascii import hexlify
import json
from flask import request
from .decorators import require_basic_or_oauth, statistician_filter_valid, gateway_belong_to_user
from userver.object.stat_gateway import Statistician
from userver.object.gateway import Gateway
from . import api, root


@api.route(root + 'gateways/<gateway_id>/statistician/hourly', methods=['GET'])
@require_basic_or_oauth
@gateway_belong_to_user
def gateway_statistician_hourly(user, gateway):
    statistician = Statistician(gateway.id)
    hourly = statistician.count_in_hourly()
    return json.dumps(hourly), 200


@api.route(root + 'gateways/<gateway_id>/statistician/daily', methods=['GET'])
@require_basic_or_oauth
@gateway_belong_to_user
def gateway_statistician_daily(user, gateway):
    statistician = Statistician(gateway.id)
    daily = statistician.count_in_daily()
    return json.dumps(daily), 200


@api.route(root + 'statistician/gateways', methods=['GET'])
@require_basic_or_oauth
@statistician_filter_valid
def statistician_gateway(user, gateway=None, start_ts=0, end_ts=-1):
    if request.method == 'GET':
        if gateway is not None:
            dnlink = Statistician.count_link(gateway.id, category='DN', start_ts=start_ts, end_ts=end_ts)
            uplink = Statistician.count_link(gateway.id, category='UP', start_ts=start_ts, end_ts=end_ts)
            return json.dumps({'uplink': uplink, 'dnlink': dnlink}), 200
        else:
            info = []
            gateways = Gateway.query.filter_by(user_id=user.id)
            for gateway in gateways:
                dnlink = Statistician.count_link(gateway.id, category='DN', start_ts=start_ts, end_ts=end_ts)
                uplink = Statistician.count_link(gateway.id, category='UP', start_ts=start_ts, end_ts=end_ts)
                info.append({'uplink': uplink, 'dnlink': dnlink, 'id':hexlify(gateway.id).decode()})
            return json.dumps(info), 200


@api.route(root+'statistician/gateways/online', methods=['GET'])
@require_basic_or_oauth
@statistician_filter_valid
def statistician_gateway_online(user, gateway=None, start_ts=0, end_ts=-1):
    if gateway is not None:
        p_list = Statistician.count_online(gateway.id)
        return json.dumps({'online': p_list}), 200
    else:
        info = []
        gateways = Gateway.query.filter_by(user_id=user.id)
        for gateway in gateways:
            p_list = Statistician.count_online(gateway.id)
            info.append({'online': p_list, 'id': hexlify(gateway.id).decode()})
        return json.dumps(info), 200



