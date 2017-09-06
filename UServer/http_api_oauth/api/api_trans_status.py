import json
from flask import request
from userver.object.trans_status import TransStatus
from .decorators import trans_status_filter, require_basic_or_oauth
from . import api, root


@api.route(root+'trans-status', methods=['GET'])
@require_basic_or_oauth
@trans_status_filter
def trans_status(user, device=None, gateway=None):
    if request.method == 'GET':
        if device is not None:
            trans_status = TransStatus.objects.all_dict(dev_eui=device.dev_eui)
        elif gateway is not None:
            trans_status = TransStatus.objects.all_dict(gateway_id=gateway.id)
        return json.dumps(trans_status), 200



