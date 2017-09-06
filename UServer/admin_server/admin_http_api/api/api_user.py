import json

from . import api, root
from flask import request, Response
from userver.user.models import User
from ..http_auth import auth
from .decorators import resource_not_exist


@api.route(root + 'users', methods=['GET', 'POST'])
@auth.auth_required
def user_list():
    if request.method == 'GET':
        users = User.query.all()
        user_dict = []
        for user in users:
            user_dict.append(user.obj_to_dict())
        return Response(status=200, response=json.dumps(user_dict))
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


@api.route(root + 'users/<user_id>', methods=['GET', 'PATCH', 'DELETE'])
@auth.auth_required
def user_index(user_id):
    if request.method == 'GET':
        user = User.query.get(user_id)
        if user is not None:
            return Response(status=200, response=json.dumps(user.obj_to_dict()))
        else:
            return resource_not_exist('User', user_id)
    elif request.method == 'DELETE':
        user = User.query.get(user_id)
        if user is not None:

            return Response(status=200, response=json.dumps(user.obj_to_dict()))
        else:
            return resource_not_exist('User', user_id)
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