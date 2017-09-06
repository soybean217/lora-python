from ..http_auth import auth
from binascii import hexlify
import json
from flask import request
from .decorators import statistician_filter_valid
from userver.object.statistician_gateway import Statistician
from userver.object.gateway import Gateway
from . import api, root


@api.route(root+'statistician/gateways', methods=['GET'])
@auth.auth_required
@statistician_filter_valid
def statistician_gateway(user=None, gateway=None, start_ts=0, end_ts=-1):
    if request.method == 'GET':
        if gateway is not None:
            dnlink = Statistician.count_link(gateway.id, category='DN', start_ts=start_ts, end_ts=end_ts)
            uplink = Statistician.count_link(gateway.id, category='UP', start_ts=start_ts, end_ts=end_ts)
            return json.dumps({'uplink': uplink, 'dnlink': dnlink}), 200
        elif user is not None:
            gateways = Gateway.query.filter_by(user_id=user.id)
        else:
            gateways = Gateway.query.all()
        info = []
        for gateway in gateways:
            dnlink = Statistician.count_link(gateway.id, category='DN', start_ts=start_ts, end_ts=end_ts)
            uplink = Statistician.count_link(gateway.id, category='UP', start_ts=start_ts, end_ts=end_ts)
            info.append({'uplink': uplink, 'dnlink': dnlink, 'id':hexlify(gateway.id).decode()})
        return json.dumps(info), 200

