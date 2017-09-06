import json
from wtforms import ValidationError

from userver.object.application import Application
from . import api, root
from flask import request, Response
from userver.object.group import Group
from binascii import hexlify
from utils.errors import KeyDuplicateError, PatchError
from .decorators import group_filter_valid, group_exists
from .forms import get_formdata_from_json_or_form
from .forms.form_group import AddGroupForm, PatchGroup, device_operate
from ..http_auth import auth


@api.route(root + 'groups', methods=['GET'])
@auth.auth_required
@group_filter_valid
def group_list(user=None, app=None):
    if request.method == 'GET':
        if app is not None:
            groups = Group.objects.all(app_eui=app.app_eui)
        elif user is not None:
            groups = []
            apps = Application.query.filter_by(user_id=user.id)
            for app in apps:
                groups += Group.objects.all(app.app_eui)
        else:
            groups = Group.objects.all()
        groups = [group.obj_to_dict() for group in groups]
        groups_json = json.dumps(groups)
        return Response(status=200, response=groups_json)
    # elif request.method == 'POST':
    #     formdata = get_formdata_from_json_or_form(request)
    #     add_group = AddGroupForm(formdata)
    #     try:
    #         if add_group.validate():
    #             if len(add_group['appskey'].data) != 0:
    #                 group = Group(add_group['app_eui'].data, add_group['name'].data, add_group['addr'].data, add_group['nwkskey'].data, appskey=add_group['appskey'].data)
    #             else:
    #                 group = Group(add_group['app_eui'].data, add_group['name'].data, add_group['addr'].data, add_group['nwkskey'].data)
    #             group.save()
    #             return Response(status=201, response=json.dumps(group.obj_to_dict()))
    #         else:
    #             return Response(status=406, response=json.dumps({'errors': add_group.errors,
    #                                                              'succeed': False}))
    #     except KeyDuplicateError as error:
    #         return Response(status=403, response=json.dumps({"error": str(error),
    #                                                          "succeed": False}))


@api.route(root + 'groups/<group_id>', methods=['GET'])
@auth.auth_required
@group_exists
def group_index(group):
    if request.method == 'GET':
        group_json = json.dumps(group.obj_to_dict())
        return group_json, 200
    # elif request.method == 'PATCH':
    #     try:
    #         formdata = get_formdata_from_json_or_form(request)
    #         PatchGroup.patch(group, formdata)
    #         return Response(status=200, response=json.dumps(group.obj_to_dict()))
    #     except (AssertionError, ValidationError, PatchError) as e:
    #         return json.dumps({"error": str(e)}), 406
    # elif request.method == 'POST':
        # POST Down Msg
        # pass
    # elif request.method == 'DELETE':
    #     try:
    #         group.delete()
    #         return json.dumps({'errors': "Group: %s deleted." % hexlify(group.id).decode(),
    #                            'succeed': False}), 200
    #     except Exception as e:
    #         return json.dumps({'errors': "Fail to delete group: %s.\n%s" % (hexlify(group.id).decode(), str(e)),
    #                            'succeed': False}), 400
    # elif request.method == 'POST':
    #     formdata = get_formdata_from_json_or_form(request)
    #     error = device_operate(group, formdata)
    #     if error is None or len(error) == 0:
    #         return json.dumps({'success': True}), 200
    #     else:
    #         return json.dumps({'error': str(error)}), 406
    #
