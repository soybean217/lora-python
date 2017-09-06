from wtforms import Form, StringField, validators, FloatField, HiddenField, SubmitField, ValidationError, Field, BooleanField, IntegerField, SelectField
from wtforms.validators import StopValidation, InputRequired, Required, DataRequired

from userver.object.gateway import Platform, Gateway, Model, FrequencyPlan
from binascii import unhexlify, hexlify
from binascii import Error as hex_error
from utils.errors import KeyDuplicateError, PatchError

from .validators import FREQ_PLAN, freq_plan_validate


def eui_48_validate(form, field):
    try:
        if len(field.data) != 12:
            raise ValueError
        field.data = unhexlify(field.data)
    except (ValueError, hex_error):
        raise StopValidation('%s:%s is not valid. Expect 12 hex digits.' % (field.name, field.data))


def platform_validate(form, field):
    field.data = Platform(field.data)


def latitude_validate(form, field):
    if field.data > 90 or field.data < -90:
        raise StopValidation('%s is not a valid %s' % (field.data, field.name))


def longitude_validate(form, field):
    if field.data > 180 or field.data < -180:
        raise StopValidation('%s is not a valid %s' % (field.data, field.name))


def model_validate(form, field):
    # try:
    #     if form['platform'].data == Platform.rpi or form['platform'].data == 'Raspberry Pi':
    #         field.data = Model.rpi(field.data)
    #     elif form['platform'].data == Platform.ll or form['platform'].data == 'LinkLabs':
    #         raise StopValidation('LinkLabs:%s is not supported so far.' % field.data)
    # except ValueError as e:
    #     raise StopValidation(str(e))
    field.data = Model(field.data)


class AnyThingRequired(DataRequired):
    def __call__(self, form, field):
        if field.data is None:
            if self.message is None:
                message = field.gettext('This field is required.')
            else:
                message = self.message

            field.errors[:] = []
            raise StopValidation(message)


class AddGatewayForm(Form):
    name = StringField('Gateway Name', validators=[validators.Optional(strip_whitespace=True)])
    mac_addr = StringField('Mac Addr', validators=[validators.InputRequired('mac_addr is required'), eui_48_validate])
    platform = StringField('Platform', validators=[validators.InputRequired('platform is required'), platform_validate])
    latitude = FloatField('Latitude', validators=[AnyThingRequired(message='latitude is Required.'), latitude_validate,])
    longitude = FloatField('Longitude', validators=[AnyThingRequired(message='longitude is Required.'), longitude_validate,])
    altitude = IntegerField('Altitude', validators=[AnyThingRequired(message='altitude is Required.')])
    model = StringField('Model', validators=[validators.InputRequired('model is required'), model_validate])
    freq_plan = StringField('Frequency Plan', validators=[validators.DataRequired('freq_plan is required'), freq_plan_validate])


def lng_handler(data):
    data = float(data)
    if data > 180 or data < -180:
        raise ValueError('%s is not a valid longitude' % data)
    return data

def lat_handler(data):
    data = float(data)
    if data > 90 or data < -90:
        raise ValueError('%s is not a valid longitude' % data)
    return data


def alt_handler(data):
    data = int(data)
    return data


class PatchGateway:
    __fields = ('name', 'freq_plan', 'public', 'disable', 'platform', 'model', 'location')
    __location_fields = {'lng': lng_handler, 'lat': lat_handler, 'alt': alt_handler}

    @classmethod
    def patch(cls, gateway, kwargs):
        for name, value in kwargs.items():
            if name in cls.__fields:
                if name == 'location':
                    for k, v in value.items():
                        handler = cls.__location_fields.get(k)
                        if handler:
                            v = handler(v)
                            setattr(gateway.location, k, v)
                        else:
                            raise PatchError('gateway', name)
                        setattr(gateway.location, k, v)
                else:
                    if name == 'freq_plan':
                        value = FrequencyPlan(value)
                    elif name == 'platform':
                        value = Platform(value)
                    elif name == 'model':
                        value = Model(value)
                    setattr(gateway, name, value)
        gateway.update()