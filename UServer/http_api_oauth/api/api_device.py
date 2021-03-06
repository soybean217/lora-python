import os

import xlrd
import time
from wtforms import ValidationError
from flask import request, Response, send_file
from binascii import unhexlify, hexlify
import json
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from .decorators import device_belong_to_user, device_filter_valid, require_basic_or_oauth
from userver.object.application import Application, generate_random_token
from userver.object.device import Device, ActiveMode, JoinDevice
from userver.object.statistician import Statistician, ConstStatis
from userver.object.mac_cmd import DevStatusReq, DutyCycleReq, RXParamSetupReq, RXTimingSetupReq
from utils.errors import KeyDuplicateError
from utils.log import Logger, Action, Resource
from . import api, root
from .forms.form_device import ABPDev, OTAADev, PatchDeviceForm
from .forms import get_formdata_from_json_or_form
from database.db_sql import db_sql


@api.route(root + 'devices/<dev_eui>/statistician/daily', methods=['GET', 'POST'])
@require_basic_or_oauth
@device_belong_to_user
def device_statistician_daily(user, app, device):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    statistician = Statistician(
        hexlify(device.dev_eui).decode(), ConstStatis.dev)
    msg_up = statistician.msg_up_count_in_daily()
    msg_down = statistician.msg_down_count_in_daily()
    msg_retrans = statistician.msg_retrans_count_in_daily()
    return json.dumps([{'name': 'uplink', 'data': msg_up}, {'name': 'retrans', 'data': msg_retrans}, {'name': 'downlink', 'data': msg_down}]), 200


@api.route(root + 'devices/<dev_eui>/statistician/hourly', methods=['GET', 'POST'])
@require_basic_or_oauth
@device_belong_to_user
def device_statistician_hourly(user, app, device):
    """
    :param dev_eui: dev_eui
    :return: 返回上行下行统计数据
    """
    statistician = Statistician(
        hexlify(device.dev_eui).decode(), ConstStatis.dev)
    msg_up = statistician.msg_up_count_in_hour()
    msg_down = statistician.msg_down_count_in_hour()
    msg_retrans = statistician.msg_retrans_count_in_hour()
    return json.dumps([{'name': 'uplink', 'data': msg_up}, {'name': 'retrans', 'data': msg_retrans}, {'name': 'downlink', 'data': msg_down}]), 200


@api.route(root + 'devices', methods=['GET', 'PATCH', 'DELETE', 'POST'])
@require_basic_or_oauth
@device_filter_valid
def devices(user, app=None, group=None, *args, **kwargs):
    if request.method == 'GET':
        time0 = time.time()
        if group is not None:
            devices = Device.objects.all(group_id=group.id)
            Logger.info('chenxing', 'devices', str(devices))
        elif app is not None:
            _group = request.args.get('!group')
            if _group is not None:
                group_devices = Device.objects.all(group_id=unhexlify(_group))
                devices = set(app.devices) - set(group_devices)
            else:
                devices = app.devices
        else:
            devices = Device.query.join(Application, Device.app_eui == Application.app_eui).filter(
                Application.user_id == user.id).order_by(Device.app_eui)
            time1 = time.time()
        # device_list = []
        # for i,v in enumerate(devices):
        #     device_list.append(v.obj_to_dict())
        Logger.info('fuming', 'devices', str(devices))
        devices = [device.obj_to_dict() for device in devices]
        devices_json = json.dumps(devices)
        return devices_json, 200
    if request.method == 'POST':
        formdata = get_formdata_from_json_or_form(request)
        try:
            active_mode = ActiveMode(formdata.get('active_mode'))
        except ValueError:
            return json.dumps({'error': {'active_mode': 'active_mode is required and should be abp or otaa'}}), 406
        if active_mode == ActiveMode.otaa:
            formdata = OTAADev(formdata)
        else:
            formdata = ABPDev(formdata)
        if formdata.validate():
            app = Application.query.get(formdata.app_eui.data)
            if app is None or app.user_id != user.id:
                return json.dumps({'errors': {'app_eui': ['You don\'t have Application %s' % hexlify(formdata.app_eui.data).decode(), ]}, }), 409
            device = Device(dev_eui=formdata.dev_eui.data, app_eui=formdata.app_eui.data,
                            name=formdata.name.data, active_mode=active_mode)
            try:
                db_sql.session.add(device)
                db_sql.session.flush()
            except IntegrityError as error:
                Logger.error(action=Action.post, resource=Resource.device,
                             id=device.dev_eui, msg=str(error))
                return json.dumps({'errors': {'dev_eui': ['Device %s already exists' % hexlify(device.dev_eui).decode(), ]}}), 409
            if active_mode == ActiveMode.otaa:
                appkey = formdata['appkey'].data
                if not appkey:
                    appkey = generate_random_token()
                try:
                    # ----------------------tmp-----------------
                    if JoinDevice.query.filter_by(appkey=appkey).first():
                        raise Exception(
                            'Appkey:%s has arleady been used. If you are not sure if your appkey is unique or not, just left it blank. System will assign an unique key for you.' % hexlify(appkey).decode())
                    # ----------------------tmp-----------------
                    db_sql.session.add(JoinDevice(
                        dev_eui=device.dev_eui, appkey=appkey))
                    db_sql.session.flush()
                except IntegrityError as error:
                    Logger.error(
                        action=Action.post, resource=Resource.device, id=device.dev_eui, msg=str(error))
                    return json.dumps({'errors': {'appkey':
                                                  ['appkey should be unique. If you are not sure if your appkey is unique or not, just left it blank. System will assign an unique key for you.']}}), 406
                except Exception as error:
                    Logger.error(
                        action=Action.post, resource=Resource.device, id=device.dev_eui, msg=str(error))
                    return json.dumps({'errors': {'appkey': [str(error)]}}), 409
            elif active_mode == ActiveMode.abp:
                try:
                    device.active(
                        addr=formdata.addr.data, nwkskey=formdata.nwkskey.data, appskey=formdata.appskey.data)
                    device.active_at = datetime.utcnow()
                except KeyDuplicateError as error:
                    return json.dumps({'errors': {'addr': [str(error)]}}), 409
            db_sql.session.commit()
            db_sql.session.registry.clear()
            device = Device.query.get(device.dev_eui)
            return json.dumps(device.obj_to_dict()), 201
        else:
            return json.dumps({'errors': formdata.errors}), 406


@api.route(root + 'devices/<dev_eui>', methods=['GET', 'PATCH', 'DELETE', 'POST'])
@require_basic_or_oauth
@device_belong_to_user
def device(user, app, device):
    if request.method == 'GET':
        return json.dumps(device.obj_to_dict()), 200
    elif request.method == 'PATCH':
        try:
            formdata = get_formdata_from_json_or_form(request)
            formdata = PatchDeviceForm(formdata)
            if formdata.validator():
                try:
                    for field in formdata.fields:
                        if field.name == 'que_down':
                            device.que_down.clear()
                        elif field.name == 'appkey':
                            if field.data is None:
                                device.join_device = None
                            else:
                                if (not device.join_device) or device.join_device.appkey != field.data:
                                    if JoinDevice.query.filter_by(appkey=field.data).first():
                                        raise Exception('Appkey:%s has arleady been used. If you are not sure if your appkey is unique or not, just left it blank. System will assign an unique key for you.' % hexlify(
                                            field.data).decode())
                                    if device.join_device is None:
                                        db_sql.session.add(JoinDevice(
                                            dev_eui=device.dev_eui, appkey=field.data))
                                    else:
                                        device.join_device.appkey = field.data
                        else:
                            setattr(device, field.name, field.data)
                    device.update(formdata.fields)
                    db_sql.session.commit()
                except IntegrityError as error:
                    Logger.error(
                        action=Action.post, resource=Resource.device, id=device.dev_eui, msg=str(error))
                    return json.dumps({'errors': {'appkey':
                                                  ['Appkey should be unique.']}}), 409
                except Exception as error:
                    Logger.error(
                        action=Action.post, resource=Resource.device, id=device.dev_eui, msg=str(error))
                    return json.dumps({'errors': {'appkey': [str(error)]}}), 409
                db_sql.session.registry.clear()
                device = Device.query.get(device.dev_eui)
                return Response(status=200, response=json.dumps(device.obj_to_dict()))
            else:
                return json.dumps({'errors': formdata.errors}), 406
        except (AssertionError, ValidationError, ValueError) as e:
            return json.dumps({"error": str(e)}), 406
    elif request.method == 'DELETE':
        try:
            device.delete()
            return Response(status=200, response=json.dumps({'succeed': True,
                                                             'dev_eui': hexlify(device.dev_eui).decode(),
                                                             }))
        except Exception as e:
            return Response(status=400, response=json.dumps(str(e)))
    elif request.method == 'POST':
        formdata = get_formdata_from_json_or_form(request)
        if not device.active_at:
            return json.dumps({'error': 'Device is not ACTIVE'}), 406
        if formdata and formdata.get('cmd') is not None:
            if formdata['cmd'] == 'DevStatusReq':
                DevStatusReq(device).push_into_que()
                return 'DevStatusReq Command is prepared to be sent now. Battery and SNR will be updated shortly', 200
            elif formdata['cmd'] == 'DutyCycleReq':
                try:
                    MaxDutyCycle = formdata.get('MaxDutyCycle')
                    MaxDutyCycle = int(MaxDutyCycle) if MaxDutyCycle else 0
                    DutyCycleReq(
                        device, MaxDutyCycle=MaxDutyCycle).push_into_que()
                except AssertionError as error:
                    return json.dumps({'error': str(error)}), 406
                except ValueError as error:
                    return json.dumps({'error': 'MaxDutyCycle should be Integer'}), 406
                return 'DutyCycleReq Command is prepared to be sent now. MaxDutyCycle will be updated shortly', 200
            elif formdata['cmd'] == 'RXParamSetupReq':
                try:
                    RX1DRoffset = formdata.get('RX1DRoffset')
                    RX1DRoffset = int(RX1DRoffset) if RX1DRoffset else None
                    RX2DataRate = formdata.get('RX2DataRate')
                    RX2DataRate = int(RX2DataRate) if RX2DataRate else None
                    RX2Frequency = formdata.get('RX2Frequency')
                    RX2Frequency = float(
                        RX2Frequency) if RX2Frequency else None
                    RXParamSetupReq(device, RX1DRoffset,
                                    RX2DataRate, RX2Frequency).push_into_que()
                except AssertionError as error:
                    return json.dumps({'error': str(error)}), 406
                except ValueError as error:
                    return json.dumps({'error': 'RX1DRoffset, RX2DataRate and RX2Frequency should be Number'}), 406
                return 'RXParamSetupReq command is prepared to be sent now. RX1DRoffset, RX2DataRate and RX2Frequency will be updated shortly', 200
            elif formdata['cmd'] == 'RXTimingSetupReq':
                try:
                    delay = formdata.get('RxDelay')
                    delay = int(delay) if delay else None
                    RXTimingSetupReq(device, delay).push_into_que()
                except AssertionError as error:
                    return json.dumps({'error': str(error)}), 406
                except ValueError as error:
                    return json.dumps({'error': 'RxDelay should be Integer'}), 406
                return 'RXTimingSetupReq command is prepared to be sent now. RxDelay will be updated shortly', 200
            elif formdata['cmd'] == 'ResetAllMacInfo':
                device.delete_mac_info()
                return 'All MAC info has been Removed', 200
            else:
                return 'Unknown cmd %s ' % formdata['cmd'], 406
        else:
            return '', 406


@api.route(root + 'devices/batch', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@require_basic_or_oauth
def Batch(user):
    if request.method == 'GET':
        return send_file('/home/kevin/lora_server/UServer/templates/batch_import.xlsx')
    elif request.method == 'POST':
        file = request.files['upload']
        if file and allowed_file(file.filename):
            filename = '%d-%d.xls' % (user.id, time.time())
            file.save(os.path.join('./uploads', filename))
            # process the file
            xls_file = open(os.path.join('./uploads', filename))
            lines = xls_file.readlines()
            # 'uploads/2-1467622415.xlsx')
            workbook = xlrd.open_workbook(filename='./uploads/' + filename)
            table = workbook.sheets()[0]
            row = table.row_values(1)
        return Response(status=200, response=open('/home/kevin/lora_server/UServer/templates/batch_feedback.xlsx', 'rb'))
    return Response(status=405, response=json.dumps("This method is not allowed in this path."))


def allowed_file(filename):
    if '.' in filename and filename.rsplit('.', 1)[1] in ('xlsx', 'xls'):
        return True
    else:
        return Response(status=415, response=json.dumps(filename + " is not supported. Except '.xlsx' file."))
