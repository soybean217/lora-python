import json

from . import api, root
from .decorators import gateway_belong_to_user, require_basic_or_oauth
from userver.object.gateway import Gateway, Location
from utils.errors import KeyDuplicateError, PatchError
from .forms.form_gateway import AddGatewayForm, PatchGateway
from flask import request, Response
from .forms import get_formdata_from_json_or_form


@api.route(root + 'gateways', methods=['GET', 'POST'])
@require_basic_or_oauth
def gateways(user):
    if request.method == 'GET':
        gateways_list = []
        gateways = Gateway.query.filter_by(user_id=user.id)
        for gateway in gateways:
            dict = gateway.obj_to_dict()
            gateways_list.append(dict)
        data = json.dumps(gateways_list)
        return Response(status=200, response=data)
    elif request.method == 'POST':
        formdata = get_formdata_from_json_or_form(request)
        add_gateway = AddGatewayForm(formdata)
        if add_gateway.validate():
            try:
                gateway = import_gateway(user, add_gateway)
                gateway.save()
                new_gateway = Gateway.query.get(gateway.id)
                return Response(status=201, response=json.dumps(new_gateway.obj_to_dict()))
            except KeyDuplicateError as error:
                errors = {'mac_addr': str(error)}
                return Response(status=406, response=json.dumps({"errors": errors}))
            except AssertionError as error:
                return Response(status=406, response=json.dumps({"errors": {"other": str(error)}}))
        else:
            errors = {}
            for key, value in add_gateway.errors.items():
                errors[key] = value[0]
            return Response(status=406, response=json.dumps({"errors": errors}))


@api.route(root + 'gateways/<gateway_id>/pull_info', methods=['GET'])
@require_basic_or_oauth
@gateway_belong_to_user
def gateway_pull_info(user, gateway):
    """
    :param user:
    :param gateway:
    :return:
    """
    gateway.get_pull_info()


@api.route(root + 'gateways/<gateway_id>', methods=['GET', 'DELETE', 'PATCH', 'POST'])
@require_basic_or_oauth
@gateway_belong_to_user
def gateway(user, gateway):
    if request.method == 'GET':
        return Response(status=200, response=json.dumps(gateway.obj_to_dict()))
    elif request.method == 'PATCH':
        try:
            formdata = get_formdata_from_json_or_form(request)
            PatchGateway.patch(gateway, formdata)
            return json.dumps(gateway.obj_to_dict()), 200
        except (AssertionError, PatchError, ValueError) as error:
            return json.dumps({'errors': str(error)}), 406
    elif request.method == 'DELETE':
        gateway.delete()
        return json.dumps({'success': True}), 200
    elif request.method == 'POST':
        formdata = get_formdata_from_json_or_form(request)
        if formdata and formdata.get('cmd') is not None:
            if formdata['cmd'] == 'restart':
                gateway.send_restart_request()
                return '', 204
            else:
                return 'Unknown cmd %s ' % formdata['cmd'], 406
        else:
            return '', 406


def import_gateway(user, add_gateway):
    mac_addr = add_gateway['mac_addr'].data
    name = add_gateway['name'].data
    platform = add_gateway['platform'].data
    freq_plan = add_gateway['freq_plan'].data
    model = add_gateway['model'].data
    location = Location(add_gateway['longitude'].data, add_gateway['latitude'].data, add_gateway['altitude'].data)
    return Gateway(user.id, mac_addr, name, platform, model, freq_plan=freq_plan, location=location)