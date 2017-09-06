from functools import wraps
from flask import request, Response
from userver.object.application import Application
from binascii import unhexlify, hexlify
from binascii import Error as hex_error

from userver.object.device import Device
from userver.object.gateway import Gateway
from userver.object.group import Group
from userver.user.models import User
from utils.utils import validate_number

expiration_in_seconds = 300


class ResourceName:
    app = 'application'
    gateway = 'gateway'
    device = 'device'
    group = 'group'
    user = 'user'


# def check_auth(username, password):
#     """This function is called to check if a username /
#     password combination is valid.
#     """
#     app_eui = unhexlify(username)
#     app = Application.query.get(app_eui)
#     return app.auth_token(password)
#
#
# def authenticate():
#     """Sends a 401 response that enables basic auth"""
#     return Response(
#         'Could not verify your access level for that URL.\n '
#         'You have to login with proper credentials', 401,
#         {'WWW-Authenticate': 'Basic realm="Login Required"'})
#
#
# def requires_auth(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         auth = request.headers.get('HTTP_AUTHORIZATION')
#         if not auth:
#             return authenticate()
#         try:
#             check_auth(auth.username, auth.password)
#         except Exception as error:
#             return Response(response='Auth Failed.\n'
#                                      '%s.' % error,
#                             status=401,
#                             headers={'WWW-Authenticate': 'Basic realm="Login Required"'})
#
#         return f(*args, **kwargs)
#     return decorated


def statistician_filter_valid(f):
    @wraps(f)
    def func_wrapper(*args, **kwargs):
        gateway_id = request.args.get('gateway')
        user_id = request.args.get('user')
        start_ts = validate_number(request.args.get('start_ts', 0))
        if start_ts is False:
            return params_type_error(start_ts, request.args.get('start_ts'), 'int')
        else:
            start_ts = int(start_ts)
        end_ts = validate_number(request.args.get('end_ts', -1))
        if end_ts is False:
            return params_type_error(end_ts, request.args.get('end_ts'), 'int')
        else:
            end_ts = int(end_ts)
        if gateway_id is not None:
            if not validate_eui(gateway_id):
                return eui_error(ResourceName.gateway, gateway_id)
            bytes_dev_eui = unhexlify(gateway_id)
            gateway = Gateway.query.get(bytes_dev_eui)
            return f(gateway=gateway, start_ts=start_ts, end_ts=end_ts)
        elif user_id is not None:
            user = User.query.get(user_id)
            if not user:
                return resource_not_exist(ResourceName.user, user_id)
            return f(user, start_ts=start_ts, end_ts=end_ts)
        else:
            return f(start_ts=start_ts, end_ts=end_ts)
    return func_wrapper


def app_exists(f):
    @wraps(f)
    def func_wrapper(app_eui, *args, **kwargs):
        app_eui = validate_eui(app_eui)
        if app_eui is None:
            return eui_error(ResourceName.app, app_eui)
        else:
            app = Application.query.get(app_eui)
            if app is None:
                return resource_not_exist(ResourceName.app, app_eui)
            return f(app)
    return func_wrapper


def device_exists(f):
    @wraps(f)
    def func_wrapper(dev_eui, *args, **kwargs):
        dev_eui = validate_eui(dev_eui)
        if dev_eui is None:
            return eui_error(ResourceName.device, dev_eui)
        else:
            device = Device.query.get(dev_eui)
            if device is None:
                return resource_not_exist(ResourceName.device, dev_eui)
            return f(device)
    return func_wrapper


def group_exists(f):
    @wraps(f)
    def func_wrapper(group_id, *args, **kwargs):
        group_id = validate_eui(group_id)
        if group_id is None:
            return eui_error(ResourceName.group, group_id)
        else:
            group = Group.objects.get(group_id)
            if group is None:
                return resource_not_exist(ResourceName.group, group)
            return f(group)
    return func_wrapper


def gateway_exists(f):
    @wraps(f)
    def func_wrapper(gateway_id, *args, **kwargs):
        gateway_id = validate_eui(gateway_id)
        if gateway_id is None:
            return eui_error(ResourceName.gateway, gateway_id)
        else:
            gateway = Gateway.query.get(gateway_id)
            if gateway is None:
                return resource_not_exist(ResourceName.gateway, gateway_id)
            return f(gateway)
    return func_wrapper


def device_filter_valid(f):
    @wraps(f)
    def func_wrapper(*args, **kwargs):
        group_id = request.args.get('group')
        app_eui = request.args.get('app')
        user_id = request.args.get('user')
        if group_id is not None:
            group_id = validate_eui(group_id)
            if not group_id:
                return eui_error(ResourceName.group, group_id)
            group = Group.objects.get(group_id)
            if group is None:
                return resource_not_exist(ResourceName.group, group_id)
            return f(group=group)
        elif app_eui is not None:
            app_eui = validate_eui(app_eui)
            if not app_eui:
                return eui_error(ResourceName.app, app_eui)
            app = Application.query.get(app_eui)
            if app is None:
                return resource_not_exist(ResourceName.app, app_eui)
            return f(app=app)
        elif user_id is not None:
            user = User.query.get(user_id)
            if user is None:
                return resource_not_exist(ResourceName.user, user_id)
            return f(user=user)
        else:
            return f()
    return func_wrapper


def group_filter_valid(f):
    @wraps(f)
    def func_wrapper(*args, **kwargs):
        app_eui = request.args.get('app')
        user_id = request.args.get('user')
        if app_eui is not None:
            app_eui = validate_eui(app_eui)
            if not app_eui:
                return eui_error(ResourceName.app, app_eui)
            app = Application.query.get(app_eui)
            if app is None:
                return resource_not_exist(ResourceName.app, app_eui)
            return f(app=app)
        elif user_id is not None:
            user = User.query.get(user_id)
            if user is None:
                return resource_not_exist(ResourceName.user, user_id)
            return f(user=user)
        else:
            return f()
    return func_wrapper


def msg_filter_valid(f):
    @wraps(f)
    def func_wrapper(*args, **kwargs):
        user_id = request.args.get('user')
        group_id = request.args.get('group')
        app_eui = request.args.get('app')
        dev_eui = request.args.get('device')
        start_ts = request.args.get('start_ts', 0)
        end_ts = request.args.get('end_ts', -1)
        if dev_eui is not None:
            dev_eui = validate_eui(dev_eui)
            if not dev_eui:
                return eui_error(ResourceName.device, dev_eui)
            dev = Device.query.get(dev_eui)
            return f(device=dev, start_ts=start_ts, end_ts=end_ts)
        elif group_id is not None:
            group_id = validate_eui(group_id)
            if not group_id:
                return eui_error(ResourceName.group, group_id)
            group = Group.objects.get(group_id)
            if group is None:
                return resource_not_exist(ResourceName.group, group_id)
            return f(group=group, start_ts=start_ts, end_ts=end_ts)
        elif app_eui is not None:
            app_eui = validate_eui(app_eui)
            if not app_eui:
                return eui_error(ResourceName.app, app_eui)
            app = Application.query.get(app_eui)
            return f(app=app, start_ts=start_ts, end_ts=end_ts)
        elif user_id is not None:
            user = User.query.get(user_id)
            if not user:
                return resource_not_exist(ResourceName.user, user_id)
            return f(user, start_ts=start_ts, end_ts=end_ts)

    return func_wrapper


def trans_status_filter(f):
    @wraps(f)
    def func_wrapper(*args, **kwargs):
        gateway_id = request.args.get('gateway')
        dev_eui = request.args.get('device')
        if gateway_id is not None:
            gateway_id = validate_eui(gateway_id)
            if not gateway_id:
                return eui_error(ResourceName.gateway, gateway_id)
            gateway = Gateway.objects.get(unhexlify(gateway_id))
            if gateway is None:
                return resource_not_exist(ResourceName.gateway, gateway_id)
            return f(gateway=gateway)
        elif dev_eui is not None:
            dev_eui = validate_eui(dev_eui)
            if not dev_eui:
                return eui_error(ResourceName.device, dev_eui)
            dev = Device.query.get(dev_eui)
            return f(device=dev)
        else:
            return missing_params('gateway', 'device')
    return func_wrapper


def validate_eui(eui):
    """
    :param eui: str (16 hex)
    :return:
    """
    if not isinstance(eui, str):
        return None
    if len(eui) != 16:
        return None
    try:
        return unhexlify(eui)
    except hex_error:
        return None


def resource_not_exist(name, id):
    if isinstance(id, bytes):
        id = hexlify(id).decode()
    return Response(status=404, response="%s:%s doesn't exist." % (name, id))


def app_has_no_service(app_eui, name):
    if isinstance(app_eui, bytes):
        app_eui = hexlify(app_eui).decode()
    return Response(status=404, response='App %s has no service named %s' % (app_eui, name))


def missing_params(*args):
    error_text = 'Missing Params '
    for arg in args:
        error_text = error_text + arg + ', '
    error_text.rstrip(',')
    error_text += ' in URL'
    return Response(status=406, response=error_text)


def id_error(name, id):
    if isinstance(id, bytes):
        id = hexlify(id).decode()
    return Response(status=406,
                    response="%s is not a valid %s ID. Expect 16 hex digits." % (name, id))


def eui_error(name, eui):
    if isinstance(eui, bytes):
        eui = hexlify(eui).decode()
    return Response(status=406,
                    response="%s is not a valid %s EUI. Expect 16 hex digits." % (name, eui))


def params_type_error(name, value, type):
    return Response(status=403,
                    response="%s should be %s, but got %s." % (name, type, value))
