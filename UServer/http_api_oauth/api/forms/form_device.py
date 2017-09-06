from userver.object.asserts import Assertions
from userver.object.device import FieldDevice
from utils.errors import PatchError, FieldNotExist
from wtforms import Form, StringField, validators, FloatField
from wtforms.validators import StopValidation

from userver.object.const import ClassType
from binascii import unhexlify
from .validators import eui_validator, appskey_validator, nwkskey_validator, addr_validator, appkey_validator, class_type_validator, fcnt_validator, bool_validator, addr_available


# def version_validator(form, field):
#     if not field.data:
#         field.data = Version.v1_0
#     else:
#         try:
#             field.data = Version(field.data)
#         except Exception as error:
#             raise StopValidation(str(error))


# class ABPDev(Form):
#     name = StringField("Name", validators=[validators.Optional(strip_whitespace=True)])
#     dev_eui = StringField("DevEUI", validators=[validators.InputRequired('Dev EUI is Required'), eui_validator])
#     app_eui = StringField("AppEUI", validators=[validators.InputRequired('APP EUI is Required'), eui_validator])
#     addr = StringField("DevAddr", validators=[validators.Optional(strip_whitespace=True), addr_validator], filters=[lambda x: x or None])
#     appskey = StringField("AppSKey", validators=[validators.Optional(strip_whitespace=True), appskey_validator, ], filters=[lambda x: x or None])
#     ver = FloatField("ver", validators=[version_validator])
#     nwkskey = StringField("NWKSKEY", validators=[validators.InputRequired('Nwkskey is Required'), nwkskey_validator, ])
#     nwkSEncKey = StringField("NWKSKEY", validators=[validators.InputRequired('Nwkskey is Required'), nwkskey_validator, ])
#     nwkSIntKeyUp = StringField("nwkSIntKeyUp", validators=[validators.InputRequired('Nwkskey is Required'), nwkskey_validator, ])
#     nwkSIntKeyDn = StringField("nwkSIntKeyDn", validators=[validators.InputRequired('Nwkskey is Required'), nwkskey_validator, ])
#
#     def validate(self):


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
    # ver = StringField("version", validators=[validators.Optional(strip_whitespace=True), version_validator, ], filters=[lambda x: x or None])
    appkey = StringField("AppKey", validators=[validators.Optional(strip_whitespace=True), appkey_validator, ], filters=[lambda x: x or None])
    # nwkkey = StringField("NwkKey", validators=[validators.Optional(strip_whitespace=True), appkey_validator, ], filters=[lambda x: x or None])


class Field:
    def __init__(self, name='', validators=(), nullable=False, required=False, default=None, disabled=False):
        self.name = name
        self.validators = validators
        self.nullable = nullable
        self.required = required
        self.disabled = disabled
        if default is not None:
            self.data = default

    def validate(self):
        if self.disabled:
            return True
        if hasattr(self, 'data'):
            if self.nullable is True and self.data is None:
                return True
            for validator in iter(self.validators):
                validator(None, self)
        elif self.required is True:
            raise StopValidation('%s is required' % self.name)


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
    appkey = Field(name='appkey', validators=[appkey_validator, ], nullable=True)
    # ver = Field(name='ver', validators=[version_validator, ])

    def __init__(self, kwargs):
        self.fields = []
        for name, value in kwargs.items():
            try:
                field = getattr(self, name)
                if isinstance(field, Field):
                    field.data = value
                    self.fields.append(field)
                else:
                    raise PatchError('Device', name)
            except AttributeError:
                raise PatchError('Device', name)

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


# class ABPDev:
#     name = Field("name", nullable=True, default='')
#     dev_eui = Field("dev_eui", validators=[eui_validator, ], required=True)
#     app_eui = Field("app_eui", validators=[eui_validator, ], required=True)
#     addr = Field("addr", validators=[addr_validator, ], required=True)
#     appskey = Field("appskey", validators=[appskey_validator, ])
#     # ver = Field("ver", validators=[version_validator, ], default=Version.v1_0)
#     nwkskey = Field("nwkskey", validators=[nwkskey_validator, ], required=True)
#     nwkSEncKey = Field("nwkSEncKey", validators=[nwkskey_validator, ], disabled=True)
#     nwkSIntKeyUp = Field("nwkSIntKeyUp", validators=[nwkskey_validator, ], disabled=True)
#     nwkSIntKeyDn = Field("nwkSIntKeyDn", validators=[nwkskey_validator, ], disabled=True)
#
#     def __init__(self, kwargs):
#         self.fields = []
#         for name, value in kwargs.items():
#             try:
#                 field = getattr(self, name)
#                 if isinstance(field, Field):
#                     field.data = value
#             except AttributeError:
#                 pass

    # def validate(self):
    #     self.errors = {}
    #     version = self.ver.data
    #     if version == Version.v1_0:
    #         self.nwkskey.required = True
    #         self.nwkSIntKeyDn.disabled = True
    #         self.nwkSIntKeyUp.disabled = True
    #         self.nwkSEncKey.disabled = True
    #     elif version == Version.v1_1:
    #         self.nwkSEncKey.required = True
    #         self.nwkSIntKeyDn.required = True
    #         self.nwkSIntKeyUp.required = True
    #         self.nwkskey.disabled = True
    #     for name, field in ABPDev.__dict__.items():
    #         if isinstance(field, Field):
    #             try:
    #                 field.validate()
    #             except StopValidation as error:
    #                 field.errors = str(error)
    #                 self.errors[field.name] = field.errors
    #                 return False
    #     return True
        # for field in self.fields:
        #     try:
        #         field.validate()
        #     except StopValidation as error:
        #         field.errors = [str(error), ]
        #         self.errors[field.name] = field.errors
        # if len(self.errors) == 0:
        #     return True
        # else:
        #     return False

