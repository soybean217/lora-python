from functools import wraps
from flask import request, Response, current_app
from userver.object.application import Application
from binascii import unhexlify, hexlify
from binascii import Error as hex_error
from base64 import b64decode
from userver.object.device import Device
from userver.object.gateway import Gateway
from userver.object.group import Group
from userver.user.models import User
from utils.utils import validate_number
from ..oauth import oauth
from flask import abort
import time

expiration_in_seconds = 300


class ResourceName:
    app = 'application'
    gateway = 'gateway'
    device = 'device'
    group = 'group'


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    app_eui = unhexlify(username)
    app = Application.query.get(app_eui)
    return app.auth_token(password)


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n '
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def require_basic_or_oauth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # return f(User.query.get(1), *args, **kwargs)
        auth = request.headers.get('Authorization')
        if not auth:
            return Response(response='Auth Required',
                            status=401,
                            headers={'WWW-Authenticate': 'Basic realm="Login Required"'})
        auth = auth.split(' ')
        if auth[0] == 'Bearer':
            valid, req = oauth.verify_request([])
            if valid:
                return f(req.user, *args, **kwargs)
            return Response(response='invalid_token', status=401)
        elif auth[0] == 'Basic':
            auth = b64decode(auth[1]).decode().split(':')
            user = User.query.filter_by(email=auth[0]).first()
            if user and user.verify_password(auth[1]):
                return f(user, *args, **kwargs)
            return abort(401)
        return abort(401)
    return decorated


def device_belong_to_user(f):
    @wraps(f)
    def func_wrapper(user, dev_eui):
        if validate_eui(dev_eui):
            bytes_eui = unhexlify(dev_eui)
            device = Device.query.get(bytes_eui)
            if device is None:
                return resource_not_belong_to_user(ResourceName.device, dev_eui)
            app = Application.query.get(device.app_eui)
            if app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.device, dev_eui)
            return f(user, app, device)
        else:
            return eui_error(ResourceName.device, dev_eui)
    return func_wrapper


def group_belong_to_user(f):
    @wraps(f)
    def func_wrapper(user, id):
        if validate_eui(id):
            group = Group.objects.get(unhexlify(id))
            if group is None:
                return resource_not_belong_to_user(ResourceName.group, id)
            app = Application.query.get(group.app_eui)
            if app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.group, id)
            return f(user, app, group)
        else:
            return id_error(ResourceName.group, id)
    return func_wrapper


def app_belong_to_user(f):
    @wraps(f)
    def func_wrapper(user, app_eui, *args, **kwargs):
        if validate_eui(app_eui):
            app = Application.query.get(unhexlify(app_eui))
            if app is None or user.id != app.user_id:
                return resource_not_belong_to_user(ResourceName.app, app_eui)
            elif app is None:
                return resource_not_belong_to_user(ResourceName.app, app_eui)
            else:
                return f(user, app)
        else:
            return eui_error(ResourceName.app, app_eui)
    return func_wrapper


# def app_has_service(f):
#     @wraps(f)
#     def func_wrapper(user, app, name, *arg, **kwargs):
#         service = app.get_service('name')
#         if service is not None:
#             return f(user, app, service)
#         else:
#             return app_has_no_service(app.app_eui, name)
#     return func_wrapper


def gateway_belong_to_user(f):
    @wraps(f)
    def func_wrapper(user, gateway_id, *args, **kwargs):
        if validate_eui(gateway_id):
            gateway = Gateway.query.get(unhexlify(gateway_id))
            if gateway is not None:
                if gateway.user_id == user.id:
                    return f(user, gateway)
                else:
                    return resource_not_belong_to_user(ResourceName.gateway, gateway_id)
            else:
                return resource_not_belong_to_user(ResourceName.gateway, gateway_id)
        else:
            return id_error(ResourceName.gateway, gateway_id)
    return func_wrapper


def device_filter_valid(f):
    @wraps(f)
    def func_wrapper(user, *args, **kwargs):
        time0 = time.time()
        group_id = request.args.get('group')
        app_eui = request.args.get('app')
        if group_id is not None:
            if not validate_eui(group_id):
                return eui_error(ResourceName.group, group_id)
            group_id = unhexlify(group_id)
            group = Group.objects.get(group_id)
            if group is None:
                return resource_not_belong_to_user(ResourceName.group, group_id)
            app = Application.query.get(group.app_eui)
            if app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.group, group_id)
            return f(user, app=app, group=group)
        elif app_eui is not None:
            if not validate_eui(app_eui):
                return eui_error(ResourceName.app, app_eui)
            bytes_app_eui = unhexlify(app_eui)
            app = Application.query.get(bytes_app_eui)
            if app is None or app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.app, app_eui)
            return f(user, app=app)
        else:
            time1 = time.time()
            return f(user)
    return func_wrapper


def group_filter_valid(f):
    @wraps(f)
    def func_wrapper(user, *args, **kwargs):
        app_eui = request.args.get('app')
        if app_eui is not None:
            if not validate_eui(app_eui):
                return eui_error(ResourceName.app, app_eui)
            bytes_app_eui = unhexlify(app_eui)
            app = Application.query.get(bytes_app_eui)
            if app is None or app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.app, app_eui)
            return f(user, app=app)
        else:
            return f(user)
    return func_wrapper


def msg_filter_valid(f):
    @wraps(f)
    def func_wrapper(user, *args, **kwargs):
        group_id = request.args.get('group')
        app_eui = request.args.get('app')
        dev_eui = request.args.get('device')

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
        max = validate_number(request.args.get('max', 0))
        if max is False:
            return params_type_error(max, request.args.get('max'), 'int')
        max = int(max)
        if dev_eui is not None:
            if not validate_eui(dev_eui):
                return eui_error(ResourceName.device, dev_eui)
            bytes_dev_eui = unhexlify(dev_eui)
            dev = Device.query.get(bytes_dev_eui)
            app = Application.query.get(dev.app_eui)
            if app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.device, dev_eui)
            else:
                return f(user, app=app, device=dev, start_ts=start_ts, end_ts=end_ts, max=max)
        elif group_id is not None:
            if not validate_eui(group_id):
                return eui_error(ResourceName.group, group_id)
            group_id = unhexlify(group_id)
            group = Group.objects.get(group_id)
            if group is None:
                return resource_not_belong_to_user(ResourceName.group, group_id)
            app = Application.query.get(group.app_eui)
            if app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.group, group_id)
            return f(user, app=app, group=group, start_ts=start_ts, end_ts=end_ts, max=max)
        elif app_eui is not None:
            if not validate_eui(app_eui):
                return eui_error(ResourceName.app, app_eui)
            bytes_app_eui = unhexlify(app_eui)
            app = Application.query.get(bytes_app_eui)
            if app is None or app.user_id != user.id:
                return resource_not_belong_to_user('application', app_eui)
            return f(user, app=app, start_ts=start_ts, end_ts=end_ts, max=max)

        else:
            return f(user, start_ts=start_ts, end_ts=end_ts, max=max)
    return func_wrapper


def loramote_filter_valid(f):
    @wraps(f)
    def func_wrapper(user, *args, **kwargs):
        gateway_id = request.args.get('gateway')
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
            if not gateway or (gateway.user_id != user.id and (not gateway.public)):
                return resource_not_belong_to_user(ResourceName.gateway, gateway_id)
            else:
                return f(user, gateway=gateway, start_ts=start_ts, end_ts=end_ts, *args, **kwargs)
        else:
            return f(user, start_ts=start_ts, end_ts=end_ts,  *args, **kwargs)
    return func_wrapper


def statistician_filter_valid(f):
    @wraps(f)
    def func_wrapper(user, *args, **kwargs):
        gateway_id = request.args.get('id')
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
            if gateway.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.gateway, gateway_id)
            else:
                return f(user, gateway=gateway, start_ts=start_ts, end_ts=end_ts)
        else:
            return f(user, start_ts=start_ts, end_ts=end_ts)
    return func_wrapper


def trans_status_filter(f):
    @wraps(f)
    def func_wrapper(user, *args, **kwargs):
        gateway_id = request.args.get('gateway')
        dev_eui = request.args.get('device')
        if gateway_id is not None:
            if not validate_eui(gateway_id):
                return eui_error(ResourceName.gateway, gateway_id)
            gateway = Gateway.objects.get(unhexlify(gateway_id))
            if gateway is None:
                return resource_not_belong_to_user(ResourceName.gateway, gateway_id)
            if gateway.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.gateway, gateway_id)
            return f(user, gateway=gateway)
        elif dev_eui is not None:
            if not validate_eui(dev_eui):
                return eui_error(ResourceName.device, dev_eui)
            bytes_dev_eui = unhexlify(dev_eui)
            dev = Device.query.get(bytes_dev_eui)
            app = Application.query.get(dev.app_eui)
            if app.user_id != user.id:
                return resource_not_belong_to_user(ResourceName.device, dev_eui)
            else:
                return f(user, device=dev)
        else:
            return missing_params('gateway', 'device')
    return func_wrapper


def validate_eui(eui):
    """
    :param eui: str (16 hex)
    :return:
    """
    if not isinstance(eui, str):
        return False
    if len(eui) != 16:
        return False
    try:
        unhexlify(eui)
        return True
    except hex_error:
        return False


def params_type_error(name, value, type):
    return Response(status=403,
                    response="%s should be %s, but got %s." % (name, type, value))


def resource_not_belong_to_user(name, id):
    if isinstance(id, bytes):
        id = hexlify(id).decode()
    return Response(status=403,
                    response="%s:%s doesn't belong to you." % (name, id))


def missing_params(*args):
    error_text = 'Missing Params '
    for arg in args:
        error_text = error_text + arg + ', '
    error_text.rstrip(',')
    error_text += ' in URL'
    return Response(status=404, response=error_text)


def id_error(name, id):
    if isinstance(id, bytes):
        id = hexlify(id).decode()
    return Response(status=404,
                    response="%s is not a valid %s ID. Expect 16 hex digits." % (id, name))


def eui_error(name, eui):
    if isinstance(eui, bytes):
        eui = hexlify(eui).decode()
    return Response(status=404,
                    response="%s is not a valid %s EUI. Expect 16 hex digits." % (name, eui))