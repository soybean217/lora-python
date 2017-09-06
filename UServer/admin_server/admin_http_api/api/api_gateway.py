import json

from ..api import api, root
from userver.object.gateway import Gateway, Location
from utils.errors import KeyDuplicateError, PatchError
from .forms.form_gateway import AddGatewayForm, PatchGateway
from ..http_auth import auth
from flask import request, Response
from .forms import get_formdata_from_json_or_form
# from userver.object.statistician_gateway import Statistician
from userver.object.stat_gateway import Statistician
from binascii import unhexlify
from .decorators import gateway_exists
from admin_server.admin_data_update.object.gateway import GatewayLocation
import json


@api.route(root + 'gateways', methods=['GET', 'POST'])
@auth.auth_required
def gateways():
    if request.method == 'GET':
        user_id = request.args.get('user', default=None)
        if user_id is not None:
            gateways = Gateway.query.filter_by(user_id=user_id)
        else:

            gateways = Gateway.query.order_by(Gateway.user_id)
        gateways_list = []
        for gateway in gateways:
            dict = gateway.obj_to_dict()
            gateways_list.append(dict)
        return json.dumps(gateways_list), 200
    # elif request.method == 'POST':
    #     formdata = get_formdata_from_json_or_form(request)
    #     add_gateway = AddGatewayForm(formdata)
    #     if add_gateway.validate():
    #         try:
    #             gateway = import_gateway(user, add_gateway)
    #             gateway.save()
    #             new_gateway = Gateway.query.get(gateway.id)
    #             return Response(status=201, response=json.dumps(new_gateway.obj_to_dict()))
    #         except KeyDuplicateError as error:
    #             errors = {'mac_addr': str(error)}
    #             return Response(status=406, response=json.dumps({"errors": errors}))
    #         except AssertionError as error:
    #             return Response(status=406, response=json.dumps({"errors": {"other": str(error)}}))
    #     else:
    #         errors = {}
    #         for key, value in add_gateway.errors.items():
    #             errors[key] = value[0]
    #         return Response(status=406, response=json.dumps({"errors": errors}))


@api.route(root + 'gateways/<gateway_id>/statistician/hourly', methods=['GET', 'POST'])
@auth.auth_required
@gateway_exists
def gateway_statistician_hourly(gateway):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """

    statistician = Statistician(gateway.id)
    hourly = statistician.count_in_hourly()
    return json.dumps(hourly), 200


@api.route(root + 'gateways/<gateway_id>/statistician/daily', methods=['GET', 'POST'])
@auth.auth_required
@gateway_exists
def gateway_statistician_daily(gateway):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    statistician = Statistician(gateway.id)
    daily = statistician.count_in_daily()
    return json.dumps(daily), 200


@api.route(root + 'gateways/<gateway_id>', methods=['GET', 'DELETE', 'PATCH', 'POST'])
@auth.auth_required
@gateway_exists
def gateway(gateway):
    if request.method == 'GET':
        return Response( status=200, response=json.dumps(gateway.obj_to_dict()))
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


# def import_gateway(user, add_gateway):
#     mac_addr = add_gateway['mac_addr'].data
#     name = add_gateway['name'].data
#     platform = add_gateway['platform'].data
#     freq_plan = add_gateway['freq_plan'].data
#     location = Location(add_gateway['longitude'].data, add_gateway['latitude'].data, add_gateway['altitude'].data)
#     if platform == Platform.rpi:
#         model = add_gateway['model'].data
#         return RaspBerryPiGateway(user.id, mac_addr, name, model, freq_plan=freq_plan, location=location)
#     elif platform == Platform.ll:
#         return LinkLabsGateway(user.id, mac_addr, name, freq_plan=freq_plan, location=location)

def import_gateway(user, add_gateway):
    mac_addr = add_gateway['mac_addr'].data
    name = add_gateway['name'].data
    platform = add_gateway['platform'].data
    freq_plan = add_gateway['freq_plan'].data
    model = add_gateway['model'].data
    location = Location(add_gateway['longitude'].data, add_gateway['latitude'].data, add_gateway['altitude'].data)
    return Gateway(user.id, mac_addr, name, platform, model, freq_plan=freq_plan, location=location)


@api.route(root + 'gps/gateways', methods=['GET'])
@auth.auth_required
def gateway_gps():
    if request.method == 'GET':
        code = request.args.get('code', '')
        gateway_id = request.args.get('id', '')
        if code != '':
            assert len(code) == 6 and isinstance(code, str), \
                'It should be a string or the length should be 6 code=%s' % str(code)
            code_province_url = code[:2]
            code_city_url = code[2:4]
            code_area_url = code[4:6]
            if code_city_url == '00':
                gateways_list = GatewayLocation.query_code(code_province=code_province_url)
            else:
                if code_area_url == '00':
                    gateways_list = GatewayLocation.query_code(code_province=code_province_url,
                                                               code_city=code_city_url)
                else:
                    gateways_list = GatewayLocation.query_code(code_province=code_province_url,
                                                               code_city=code_city_url,
                                                               code_area=code_area_url)
            if len(gateways_list) != 0:
                data = [{'id': i_gateway.gateway_id, 'lat': i_gateway.latitude, 'lng': i_gateway.longitude}
                        for i_gateway in gateways_list]
                return json.dumps(data), 200
            else:
                return 'There has not any gateway belong to the code.', 204
        elif gateway_id != '':
            gateway_data = GatewayLocation.query_gateway_id(gateway_id=gateway_id)
            if gateway_data is not None:
                data = {'id': gateway_id, 'lat': gateway_data.latitude, 'lng': gateway_data.longitude}
                return json.dumps(data), 200
            else:
                return 'The id of gateway does not exit.', 204
        else:
            return 'Lack of url query key.', 406
