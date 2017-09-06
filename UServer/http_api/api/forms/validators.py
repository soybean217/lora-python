from binascii import Error as hex_error
from binascii import unhexlify, hexlify
from wtforms.validators import StopValidation
from userver.object.gateway import FrequencyPlan
from utils.errors import KeyDuplicateError
import binascii

from userver.object.device import ClassType
from userver.object.addr import AddrManger

FREQ_PLAN = [(FrequencyPlan.EU863_870.value, FrequencyPlan.EU863_870.value),
             (FrequencyPlan.EU433.value, FrequencyPlan.EU433.value),
             (FrequencyPlan.CN470_510.value, FrequencyPlan.CN470_510.value),
             (FrequencyPlan.MT433.value, FrequencyPlan.MT433.value)]


def freq_plan_validate(form, field):
    field.data = FrequencyPlan(field.data)


def eui_validator(form, field):
    try:
        if len(field.data) != 16:
            raise ValueError
        field.data = unhexlify(field.data)
    except (ValueError, hex_error):
        raise StopValidation('%s is not a valid EUI. EUI should be 16 hex digits.' % field.data)


def appskey_validator(form, field):
    try:
        if len(field.data) != 32 and len(field.data) != 0:
            raise ValueError
        field.data = unhexlify(field.data)
    except (ValueError, hex_error):
        raise StopValidation('%s is not a valid %s. Expect 32 hex digits.' % (field.data, field.name))


def appkey_validator(form, field):
    try:
        if len(field.data) != 32:
            raise ValueError
        field.data = unhexlify(field.data)
    except (ValueError, hex_error):
        raise StopValidation('%s is not a valid %s. Expect 32 hex digits.' % (field.data, field.name))


def nwkskey_validator(form, field):
    try:
        if len(field.data) != 32:
            raise ValueError
        field.data = unhexlify(field.data)
    except (ValueError, hex_error):
        raise StopValidation('%s is not a valid %s. Expect 32 hex digits.' % (field.data, field.name))


def addr_validator(form, field):
    try:
        if len(field.data) != 8:
            raise ValueError
        field.data = unhexlify(field.data)
    except (ValueError, binascii.Error) as e:
        raise StopValidation('%s is not a valid %s. Expect 8 hex digits.' % (field.data, field.name))


def bool_validator(form, field):
    if not isinstance(field.data, bool):
        raise StopValidation('%s is not a valid %s. Expect boolean.' % (field.data, field.name))


def class_type_validator(form, field):
    try:
        field.data = ClassType(field.data)
    except ValueError:
        raise StopValidation('%s is not a valid %s. Expect A or B or C.' % (field.data, field.name))


def fcnt_validator(form, field):
    if not isinstance(field.data, int) or field.data < 0 or field.data > 65535:
        raise StopValidation('%s is not a valid %s. Expect 8 hex digits.' % (field.data, field.name))


def addr_available(form, field):
    try:
        AddrManger.addr_available(field.data)
    except KeyDuplicateError:
        raise StopValidation('addr %s has already been used' % hexlify(field.data))





