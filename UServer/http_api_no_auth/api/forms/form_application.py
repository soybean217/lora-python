from wtforms import Form, StringField, validators, SelectField
from .validators import FREQ_PLAN, freq_plan_validate, eui_validator, appkey_validator
from utils.errors import KeyDuplicateError, PatchError
from userver.object.gateway import FrequencyPlan
from binascii import unhexlify
from userver.object.asserts import Assertions


class AddAppForm(Form):
    name = StringField("App Name", validators=[validators.Optional(strip_whitespace=True)])
    app_eui = StringField("AppEUI", validators=[validators.DataRequired(), eui_validator, ])
    freq_plan = SelectField("Frequency Plan", choices=FREQ_PLAN, validators=[validators.DataRequired(), freq_plan_validate])
    appkey = StringField("AppKey", validators=[validators.Optional(), appkey_validator, ], filters=[lambda x: x or None])


# class PatchAppForm(Form):
#     name = StringField("Name", validators=[validators.Optional(strip_whitespace=True)])
#     freq_plan = SelectField("Frequency Plan", choices=FREQ_PLAN, validators=[validators.Optional(strip_whitespace=True), freq_plan_validate])
#     appkey = StringField("AppKey", validators=[validators.Optional(strip_whitespace=True), appkey_validator, ])
#     token = StringField("Token", validators=[validators.Optional(strip_whitespace=False)])


class PatchApp:
    __fields = ('name', 'token', 'freq_plan', 'appkey')

    @classmethod
    def patch(cls, application, kwargs):
        for name, value in kwargs.items():
            if name == 'token':
                application.generate_new_token()
            elif name in cls.__fields:
                if name == 'freq_plan':
                    value = FrequencyPlan(value)
                elif name == 'appkey':
                    Assertions.s_appkey(value)
                    if value:
                        value = unhexlify(value)
                setattr(application, name, value)
            else:
                raise PatchError('Application', name)
        application.update()