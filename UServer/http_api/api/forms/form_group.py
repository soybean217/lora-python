from binascii import unhexlify
import binascii
from wtforms import Form, StringField, validators, BooleanField, IntegerField

from userver.object.asserts import Assertions
from .validators import eui_validator, addr_validator, nwkskey_validator, appskey_validator

from userver.object.group import FieldGroup
from utils.errors import PatchError
from utils.log import Logger, Action, Resource


class AddGroupForm(Form):
    name = StringField('Group Name', validators=[validators.Optional(None)])
    app_eui = StringField("AppEUI", validators=[validators.InputRequired(None), eui_validator])
    addr = StringField('Addr', validators=[validators.InputRequired(None), addr_validator])
    nwkskey = StringField('NwkSKey', validators=[validators.InputRequired(None), nwkskey_validator])
    appskey = StringField('AppSkey', validators=[validators.Optional(True), appskey_validator, ])


class PatchGroup:
    __fields = (FieldGroup.name, FieldGroup.addr, FieldGroup.nwkskey,
                FieldGroup.appskey, FieldGroup.fcnt, 'que_down', FieldGroup.periodicity, FieldGroup.datr)

    @classmethod
    def patch(cls, device, kwargs):
        for name, value in kwargs.items():
            if name == 'que_down':
                device.que_down.clear()
            elif name in cls.__fields:
                if name == FieldGroup.addr:
                    Assertions.s_addr(value)
                    value = unhexlify(value)
                elif name == FieldGroup.appskey:
                    Assertions.s_appskey(value)
                    value = unhexlify(value)
                elif name == FieldGroup.nwkskey:
                    Assertions.s_nwkskey(value)
                    value = unhexlify(value)
                setattr(device, name, value)
            else:
                raise PatchError('Application', name)
        device.update()


def device_operate(group, form):
    for name, value in form.items():
        if name == 'ADD':
            if isinstance(value, list):
                errors = []
                for device in value:
                    try:
                        group.add_device(unhexlify(device))
                    except (KeyError, binascii.Error) as error:
                        Logger.error(resource=Resource.group, id=group.id, msg='Add Device error %s' % error)
                        errors.append(device)
                return errors
            elif isinstance(value, str):
                try:
                    group.add_device(unhexlify(value))
                except (KeyError, binascii.Error) as error:
                    Logger.error(resource=Resource.group, id=group.id, msg='Add Device error %s' % error)
                    return error
        elif name == 'REMOVE':
            if isinstance(value, list):
                errors = []
                for device in value:
                    try:
                        group.rem_device(unhexlify(device))
                    except (KeyError, binascii.Error) as error:
                        Logger.info(resource=Resource.group, id=group.id, msg='Remove Device error %s' % error)
                        errors.append(device)
                return errors
            elif isinstance(value, str):
                try:
                    group.rem_device(unhexlify(value))
                except (KeyError, binascii.Error) as error:
                    Logger.info(resource=Resource.group, id=group.id, msg='Remove Device error %s' % error)
                    return error


# def add_device_to_group(group, form):
#     for name, value in form.items():
#         if isinstance(value, list):
#             errors = []
#             for device in value:
#                 try:
#                     group.add_device(unhexlify(device))
#                 except (KeyError, binascii.Error) as error:
#                     logger.info(ConstLog.group + 'Add Device error %s' % error)
#                     errors.append(device)
#             return errors
#         elif isinstance(value, str):
#             try:
#                 group.add_device(unhexlify(value))
#             except (KeyError, binascii.Error) as error:
#                 logger.info(ConstLog.group + 'Add Device error %s' % error)
#                 return error
#
#
# def rem_device_from_group(group, form):
#     for name, value in form.items():
#         if isinstance(value, list):
#             errors = []
#             for device in value:
#                 try:
#                     group.rem_device(unhexlify(device))
#                 except (KeyError, binascii.Error) as error:
#                     logger.info(ConstLog.group + 'Remove Device error %s' % error)
#                     errors.append(device)
#             return errors
#         elif isinstance(value, str):
#             try:
#                 group.rem_device(unhexlify(value))
#             except (KeyError, binascii.Error) as error:
#                 logger.info(ConstLog.group + 'Remove Device error %s' % error)
#                 return error














# class UpForm(Form):
#     def __init__(self, formdata=None, obj=None, prefix='', **kwargs):
#         super(UpForm, self).__init__(formdata, obj)
#         up_list = []
#         if formdata is not None:
#             for name in formdata:
#                 up_list.append(name)
#         self.up_list = up_list
#
#     def check_form(self):
#         pass

# class UpGrp(UpForm):
#     addr = StringField("DevAddr", validators=[validators.Optional(True), addr_validator, ])
#     name = StringField("Device Name", validators=[validators.Optional(True)])
#     nwkskey = StringField("NWKSKEY", validators=[validators.Optional(True), key_validator, ])
#     appskey = StringField("APPSKEY", validators=[validators.Optional(True), key_validator, ])
#     rm_appskey = BooleanField("Remeve APPSKEY", validators=[validators.Optional(True), ])
#     reset_fcnt_down = BooleanField("fcnt_down", validators=[validators.Optional(True), ])
#     reset_fcnt_up = BooleanField("fcnt_up", validators=[validators.Optional(True), ])
#     periodicity = IntegerField('PingSlotPeriod', validators=[validators.Optional(True), int_validate, ping_slot_validate])
#
#     def patch(self, group):
#         for item in self.up_list:
#             if item in self._fields:
#                 if item == 'rm_appskey':
#                     group.appskey = b''
#                 elif item == 'reset_fcnt_down':
#                     group.que_down.clear()
#                 elif item == 'reset_fcnt_up':
#                     group.fcnt_up = 0
#                 else:
#                     setattr(group, item, getattr(self, item).data)
#         group.update()