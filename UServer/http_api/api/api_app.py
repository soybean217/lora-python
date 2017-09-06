import json
from binascii import hexlify

from sqlalchemy.exc import IntegrityError

from http_api.api.decorators import app_belong_to_user
from utils.errors import KeyDuplicateError, PatchError, ResourceAlreadyExistError

from .forms import get_formdata_from_json_or_form
from .forms.form_application import AddAppForm, PatchApp

from . import api, root
from flask import request, Response
from userver.object.application import Application, LocationService, HttpPush
from userver.object.group import Group
from http_api.http_auth import auth

from urllib.parse import urlparse
from time import time

from utils.log import logger
import time


@api.route(root + 'apps', methods=['GET', 'POST'])
@auth.auth_required
def app_list(user):
    if user is not None:
        if request.method == 'GET':
            logger.info('TIMESTAMP \'apps\' HTTP[GET]:%s' % time.time())
            app_dict = []
            start = time()
            applications = Application.query.filter_by(user_id=user.id).all()
            mid = time()
            logger.info('TIMESTAMP \'apps\' QueryOver:%s' % time.time())
            for application in applications:
                app_dict.append(application.obj_to_dict())
            end = time()
            return Response(status=200, response=json.dumps(app_dict))
        elif request.method == 'POST':
            logger.info('TIMESTAMP \'apps\' HTTP[POST]:%s' % time.time())
            formdata = get_formdata_from_json_or_form(request)
            add_app = AddAppForm(formdata)
            if add_app.validate():
                try:
                    logger.info('TIMESTAMP \'apps\' QueryBegin:%s' % time.time())
                    app = Application(user_id=user.id, app_eui=add_app['app_eui'].data, name=add_app['name'].data, freq_plan=add_app['freq_plan'].data, appkey=add_app['appkey'].data)
                    app.save()
                    app = Application.query.get(app.app_eui)
                    logger.info('TIMESTAMP \'apps\' QueryOver:%s' % time.time())
                    logger.info('TIMESTAMP \'apps\' SendRespond:%s' % time.time())
                    return Response(status=201, response=json.dumps(app.obj_to_dict()))
                except ResourceAlreadyExistError as e:
                    raise e
                    return Response(status=409, response=json.dumps({'error': str(e)}))
            else:
                return Response(status=406, response=json.dumps({'succeed': False,
                                                                 'errors': json.dumps(add_app.errors)}))
        return Response(status=405, response=json.dumps("This method is not allowed in this path."))
    else:
        return json.dumps({'error': 'AUTH ERROR'}), 401


@api.route(root + 'apps/<app_eui>', methods=['GET', 'PATCH', 'DELETE'])
@auth.auth_required
@app_belong_to_user
def app_index(user, app):
    if request.method == 'GET':
        logger.info('TIMESTAMP \'apps/<app_eui>\' HTTP[GET]:%s' % time.time())
        app_dict = app.obj_to_dict()
        logger.info('TIMESTAMP \'apps/<app_eui>\' obj_to_dict_over:%s' % time.time())
        json_data = json.dumps(app_dict)
        logger.info('TIMESTAMP \'apps/<app_eui>\' json_dumps_over:%s' % time.time())
        return Response(status=200, response=json_data)
    elif request.method == 'PATCH':
        logger.info('TIMESTAMP \'apps/<app_eui>\' HTTP[PATCH]:%s' % time.time())
        try:
            formdata = get_formdata_from_json_or_form(request)
            PatchApp.patch(app, formdata)
            logger.info('TIMESTAMP \'apps/<app_eui>\' SendRespond:%s' % time.time())
            return json.dumps(app.obj_to_dict()), 200
        except (AssertionError, PatchError, ValueError) as error:
            return json.dumps(str(error)), 406
    elif request.method == 'DELETE':
        logger.info('TIMESTAMP \'apps/<app_eui>\' HTTP[DELETE]:%s' % time.time())
        logger.info('TIMESTAMP \'apps\' QueryBegin(all):%s' % time.time())
        groups = Group.objects.all(app_eui=app.app_eui)
        logger.info('TIMESTAMP \'apps\' QueryOver(all):%s' % time.time())
        logger.info('TIMESTAMP \'apps\' QueryBegin(delete):%s' % time.time())
        for group in groups:
            group.delete()
        for device in app.devices:
            device.delete()
        app.delete()
        logger.info('TIMESTAMP \'apps\' QueryOver(delete):%s' % time.time())
        logger.info('TIMESTAMP \'apps/<app_eui>\' SendRespond:%s' % time.time())
        return Response(status=200, response={'succeed': True,
                                              'msg': 'App: %s already deleted.' % hexlify(app.app_eui)})
    return Response(status=405, response=json.dumps("This method is not allowed in this path."))


# @api.route(root + 'apps/<app_eui>/services', methods=['GET', 'POST'])
# @auth.auth_required
# @app_belong_to_user
# def service_list(user, app):
#     if request.method == 'GET':
#         services = []
#         if app.http_push:
#             services.append({'name': 'Http Push', 'url': app.http_push.url})
#         if app.location_service:
#             services.append({'name': 'Location Service'})
#         return Response(status=200, response=json.dumps(services))
#     # elif request.method == 'POST':
#     #     try:
#     #         formdata = get_formdata_from_json_or_form(request)
#     #         add_service = AddServiceForm(formdata)
#     return Response(status=405, response=json.dumps("This method is not allowed in this path."))

@api.route(root + 'apps/<app_eui>/http-push', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@auth.auth_required
@app_belong_to_user
def http_push_index(user, app):
    if request.method == 'GET':
        logger.info('TIMESTAMP \'apps/<app_eui>/http-push\' HTTP[GET]:%s' % time.time())
        if app.http_push:
            response = app.http_push.obj_to_dict()
            logger.info('TIMESTAMP \'apps/<app_eui>/http-push\' GET response:%s' % time.time())
        else:
            response = {'open': False}
            logger.info('TIMESTAMP \'apps/<app_eui>/http-push\' GET response:%s' % time.time())
        logger.info('TIMESTAMP \'apps/<app_eui>/http-push\' SendRespond:%s' % time.time())
        return Response(status=200, response=json.dumps(response))
    elif request.method == 'POST':
        if not app.http_push:
            try:
                formdata = get_formdata_from_json_or_form(request)
                url = formdata.get('url')
                if url:
                    url = urlparse(url)
                    if url.scheme != 'http' and url.scheme != 'https':
                        return Response(status=406, response=json.dumps({"error": "Url scheme should be http or https. Url should start with 'http://' or 'https://'"}))
                    if url.netloc == '':
                        return Response(status=406, response=json.dumps({'error': "Invalid url"}))
                    url = url.geturl()
                http_push = HttpPush(app_eui=app.app_eui, url=url)
                http_push.add()
                return Response(status=200, response=json.dumps(http_push.obj_to_dict()))
            except Exception as error:
                return Response(status=406, response=json.dumps({'error': str(error)}))
        else:
            return Response(status=406, response=json.dumps({'error': 'Http Push has already opened'}))
    elif request.method == 'PATCH':
        if app.http_push:
            try:
                formdata = get_formdata_from_json_or_form(request)
                url = formdata.get('url')
                if url:
                    url = urlparse(url)
                    if url.scheme != 'http' and url.scheme != 'https':
                        return Response(status=406, response=json.dumps({"error": "Url scheme should be http or https. Url should start with 'http://' or 'https://'"}))
                    if url.netloc == '':
                        return Response(status=406, response=json.dumps({'error': "Invliad url"}))
                    url = url.geturl()
                app.http_push.url = url
                app.http_push.update()
                return Response(status=200, response=json.dumps(app.http_push.obj_to_dict()))
            except Exception as error:
                return Response(status=406, response=json.dumps({'error': str(error)}))
        else:
            return Response(status=406, response=json.dumps({'error': 'Http Push Service is not Opened yet'}))
    elif request.method == 'DELETE':
        if app.http_push:
            app.http_push.delete()
        return Response(status=201, response=json.dumps({'open': False}))
    return Response(status=405, response=json.dumps("This method is not allowed in this path."))


@api.route(root + 'apps/<app_eui>/location-service', methods=['GET', 'POST', 'DELETE'])
@auth.auth_required
@app_belong_to_user
def location_service_index(user, app):
    if request.method == 'GET':
        logger.info('TIMESTAMP \'apps/<app_eui>/location-service\' HTTP[GET]:%s' % time.time())
        if app.location_service:
            response = {'open': True}
            logger.info('TIMESTAMP \'apps/<app_eui>/location-service\' GET response:%s' % time.time())
        else:
            response = {'open': False}
            logger.info('TIMESTAMP \'apps/<app_eui>/location-service\' GET response:%s' % time.time())
        logger.info('TIMESTAMP \'apps/<app_eui>/location-service\' SendRespond:%s' % time.time())
        return Response(status=200, response=json.dumps(response))
    elif request.method == 'POST':
        if not app.location_service:
            ls = LocationService(app_eui=app.app_eui)
            ls.add()
        return Response(status=200, response=json.dumps({'open': True}))
    elif request.method == 'DELETE':
        if app.location_service:
            app.location_service.delete()
        return Response(status=201, response=json.dumps({'open': False}))
    return Response(status=405, response=json.dumps("This method is not allowed in this path."))