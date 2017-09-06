import json
from binascii import hexlify

from sqlalchemy.exc import IntegrityError

from utils.errors import KeyDuplicateError, PatchError, ResourceAlreadyExistError

from .forms import get_formdata_from_json_or_form
from .forms.form_application import AddAppForm, PatchApp

from . import api, root
from flask import request, Response
from userver.object.application import Application, LocationService, HttpPush
from .decorators import app_exists
from ..http_auth import auth

from urllib.parse import urlparse


@api.route(root + 'apps', methods=['GET', 'POST'])
@auth.auth_required
def app_list():
    if request.method == 'GET':
        user_id = request.args.get('user', default=None)
        if user_id is not None:
            applications = Application.query.filter_by(user_id=user_id)
        else:
            applications = Application.query.order_by(Application.user_id)
        app_dict = []
        for application in applications:
            app_dict.append(application.obj_to_dict())
        return Response(status=200, response=json.dumps(app_dict))
    # elif request.method == 'POST':
    #     formdata = get_formdata_from_json_or_form(request)
    #     add_app = AddAppForm(formdata)
    #     if add_app.validate():
    #         try:
    #             app = Application(user_id=user.id, app_eui=add_app['app_eui'].data, name=add_app['name'].data, freq_plan=add_app['freq_plan'].data, appkey=add_app['appkey'].data)
    #             app.save()
    #             app = Application.query.get(app.app_eui)
    #             return Response(status=201, response=json.dumps(app.obj_to_dict()))
    #         except ResourceAlreadyExistError as e:
    #             return Response(status=409, response=json.dumps({'error': str(e)}))
    #     else:
    #         return Response(status=406, response=json.dumps({'succeed': False,
    #                                                          'errors': json.dumps(add_app.errors)}))
    return Response(status=405, response=json.dumps("This method is not allowed in this path."))


@api.route(root + 'apps/<app_eui>', methods=['GET', 'PATCH', 'DELETE'])
@auth.auth_required
@app_exists
def app_index(app):
    if request.method == 'GET':
        return Response(status=200, response=json.dumps(app.obj_to_dict()))
    # elif request.method == 'PATCH':
    #     try:
    #         formdata = get_formdata_from_json_or_form(request)
    #         PatchApp.patch(app, formdata)
    #         return json.dumps(app.obj_to_dict()), 200
    #     except (AssertionError, PatchError, ValueError) as error:
    #         return json.dumps(str(error)), 406
    # elif request.method == 'DELETE':
    #     groups = Group.objects.all(app_eui=app.app_eui)
    #     for group in groups:
    #         group.delete()
    #     for device in app.devices:
    #         device.delete()
    #     app.delete()
    #     return Response(status=200, response={'succeed': True,
    #                                           'msg': 'App: %s already deleted.' % hexlify(app.app_eui)})
    return Response(status=405, response=json.dumps("This method is not allowed in this path."))


@api.route(root + 'apps/<app_eui>/http-push', methods=['GET', 'POST', 'PATCH', 'DELETE'])
@auth.auth_required
@app_exists
def http_push_index(app):
    if request.method == 'GET':
        if app.http_push:
            response = app.http_push.obj_to_dict()
        else:
            response = {'open': False}
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
@app_exists
def location_service_index(app):
    if request.method == 'GET':
        if app.location_service:
            response = {'open': True}
        else:
            response = {'open': False}
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