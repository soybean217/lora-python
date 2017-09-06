from enum import Enum

MAX_FRMPAYLOAD_LENGTH = 50


class FieldDevice:
    dev_eui = 'dev_eui'
    name = 'name'
    nwkskey = 'nwkskey'
    nwkSEncKey = 'nwkSEncKey'
    nwkSIntKeyUp = 'nwkSIntKeyUp'
    nwkSIntKeyDn = 'nwkSIntKeyDn'
    appskey = 'appskey'
    addr = 'addr'
    fcnt_up = 'fcnt_up'
    fcnt_down = 'fcnt_down'
    dev_class = 'dev_class'
    app_eui = 'app_eui'
    adr = 'adr'
    check_fcnt = 'check_fcnt'
    rx_window = 'rx_window'
    battery = 'battery'
    snr = 'snr'
    ver = 'ver'

    appkey = 'appkey'

    active_mode = 'active_mode'
    active_at = 'active_at'

    datr = 'datr'
    periodicity = 'periodicity'


class ClassType(Enum):
    a = 'A'
    b = 'B'
    c = 'C'


class FieldGroup:
    app_eui = 'app_eui'
    name = 'name'
    nwkskey = 'nwkskey'
    appskey = 'appskey'
    addr = 'addr'
    fcnt = 'fcnt'
    periodicity = 'periodicity'
    datr = 'datr'
    id = 'id'