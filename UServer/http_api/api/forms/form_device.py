from userver.object.asserts import Assertions
from userver.object.device import FieldDevice
from utils.errors import PatchError
from wtforms import Form, StringField, validators
from wtforms.validators import StopValidation

from userver.object.const import ClassType
from binascii import unhexlify
from .validators import eui_validator, appskey_validator, nwkskey_validator, addr_validator, appkey_validator, class_type_validator, fcnt_validator, bool_validator, addr_available


class ABPDev(Form):
    name = StringField("Name", validators=[validators.Optional(strip_whitespace=True)])
    dev_eui = StringField("DevEUI", validators=[validators.InputRequired('Dev EUI is Required'), eui_validator])
    app_eui = StringField("AppEUI", validators=[validators.InputRequired('APP EUI is Required'), eui_validator])
    addr = StringField("DevAddr", validators=[validators.Optional(strip_whitespace=True), addr_validator], filters=[lambda x: x or None])
    nwkskey = StringField("NWKSKEY", validators=[validators.InputRequired('Nwkskey is Required'), nwkskey_validator, ])
    appskey = StringField("AppSKey", validators=[validators.Optional(strip_whitespace=True), appskey_validator, ], filters=[lambda x: x or None])


class OTAADev(Form):
    name = StringField("Name", validators=[validators.Optional(strip_whitespace=True)])
    dev_eui = StringField("DevEUI", validators=[validators.InputRequired('Dev EUI is Required'), eui_validator])
    app_eui = StringField("AppEUI", validators=[validators.InputRequired('APP EUI is Required'), eui_validator])
    appkey = StringField("AppKey", validators=[validators.Optional(strip_whitespace=True), appkey_validator, ], filters=[lambda x: x or None])


class Field:
    def __init__(self, name='', validators=(), nullable=False):
        self.name = name
        self.validators = validators
        self.nullable=nullable

    def validate(self):
        if self.nullable is True and self.data is None:
            return True
        else:
            for validator in iter(self.validators):
                validator(None, self)


class PatchDeviceForm:
    name = Field(name='name')
    addr = Field(name='addr', validators=[addr_validator, addr_available])
    nwkskey = Field(name='nwkskey', validators=[nwkskey_validator, ])
    appskey = Field(name='appskey', validators=[appskey_validator, ])
    dev_class = Field(name='dev_class', validators=[class_type_validator, ])
    fcnt_up = Field(name='fcnt_up', validators=[fcnt_validator, ])
    fcnt_down = Field(name='fcnt_down', validators=[fcnt_validator, ])
    que_down = Field(name='que_down')
    check_fcnt = Field(name='check_fcnt', validators=[bool_validator, ])
    adr = Field(name='adr', validators=[bool_validator, ])
    appkey = Field(name='appkey', validators=[appkey_validator,], nullable=True)

    def __init__(self, kwargs):
        self.fields = []
        for name, value in kwargs.items():
            try:
                field = getattr(self, name)
                if isinstance(field, Field):
                    field.data = value
                    self.fields.append(field)
                else:
                    raise PatchError('Application', name)
            except AttributeError:
                raise PatchError('Application', name)

    def validator(self):
        self.errors = {}
        for field in self.fields:
            try:
                field.validate()
            except StopValidation as error:
                field.errors = [str(error), ]
                self.errors[field.name] = field.errors
        if len(self.errors) == 0:
            return True
        else:
            return False



# class PatchDevice:
#     __fields = (FieldDevice.name, FieldDevice.addr, FieldDevice.nwkskey,
#                 FieldDevice.appskey, FieldDevice.dev_class, FieldDevice.fcnt_up,
#                 FieldDevice.fcnt_down, 'que_down', FieldDevice.check_fcnt, FieldDevice.adr)

    # @classmethod
    # def patch(cls, device, kwargs):
    #     for name, value in kwargs.items():
    #         if name == 'que_down':
    #             device.que_down.clear()
    #         elif name in cls.__fields:
    #             if name == FieldDevice.dev_class:
    #                 value = ClassType(value)
    #             elif name == FieldDevice.addr:
    #                 Assertions.s_addr(value)
    #                 value = unhexlify(value)
    #             elif name == FieldDevice.appskey:
    #                 Assertions.s_appskey(value)
    #                 value = unhexlify(value)
    #             elif name == FieldDevice.nwkskey:
    #                 Assertions.s_nwkskey(value)
    #                 value = unhexlify(value)
    #             setattr(device, name, value)
    #         elif name == 'appkey':
    #             if value is None:
    #                 device.join_device = None
    #             else:
    #                 device.join_device.appkey = unhexlify(value)
    #         else:
    #             raise PatchError('Application', name)
    #     device.update()

