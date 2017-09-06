import json

from http_api_no_auth.api import api, root
from http_api_no_auth.api.decorators import gateway_belong_to_user
from userver.object.gateway import Gateway, Location
from utils.errors import KeyDuplicateError, PatchError
from .forms.form_gateway import AddGatewayForm, PatchGateway
from ..http_auth import auth
from flask import request, Response
from .forms import get_formdata_from_json_or_form
from userver.object.statistician_gateway import Statistician
from utils.log import logger
import time


@api.route(root + 'gateways', methods=['GET', 'POST'])
@auth.auth_required
def gateways(user):
    if request.method == 'GET':
        logger.info('TIMESTAMP \'gateways\' HTTP[GET]:%s' % time.time())
        gateways_list = []
        logger.info('TIMESTAMP \'gateways\' QueryBegin:%s' % time.time())
        gateways = Gateway.query.filter_by(user_id=user.id)
        logger.info('TIMESTAMP \'gateways\' QueryOver:%s' % time.time())
        for gateway in gateways:
            dict = gateway.obj_to_dict()
            gateways_list.append(dict)
        logger.info('TIMESTAMP \'gateways\' obj_to_dict_Over:%s' % time.time())
        respond_data = json.dumps(gateways_list)
        logger.info('TIMESTAMP \'gateways\' obj_to_dict_Over:%s' % time.time())
        logger.info('TIMESTAMP \'gateways\' SendRespond:%s' % time.time())
        return Response(status=200, response=respond_data)
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


@api.route(root + 'gateways/<gateway_id>/statistician/hourly', methods=['GET', 'POST'])
@auth.auth_required
@gateway_belong_to_user
def gateway_statistician_hourly(user, gateway):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    logger.info('TIMESTAMP \'gateways/<gateway_id>/statistician/hourly\' HTTP[GET]:%s' % time.time())
    statistician = Statistician(gateway.id)
    hourly = statistician.count_in_hour()
    logger.info('TIMESTAMP \'gateways/<gateway_id>/statistician/hourly\' SendRespond:%s' % time.time())
    return json.dumps(hourly), 200


@api.route(root + 'gateways/<gateway_id>/statistician/daily', methods=['GET', 'POST'])
@auth.auth_required
@gateway_belong_to_user
def gateway_statistician_daily(user, gateway):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    logger.info('TIMESTAMP \'gateways/<gateway_id>/statistician/daily\' HTTP[GET]:%s' % time.time())
    statistician = Statistician(gateway.id)
    daily = statistician.count_in_daily()
    logger.info('TIMESTAMP \'gateways/<gateway_id>/statistician/daily\' SendRespond:%s' % time.time())
    return json.dumps(daily), 200


@api.route(root + 'gateways/<gateway_id>', methods=['GET', 'DELETE', 'PATCH', 'POST'])
@auth.auth_required
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