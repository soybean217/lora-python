from enum import Enum


class ClassType(Enum):
    a = 'A'
    b = 'B'
    c = 'C'


class FieldDevice:
    dev_eui = 'dev_eui'
    name = 'name'
    nwkskey = 'nwkskey'
    appskey = 'appskey'
    addr = 'addr'
    fcnt_up = 'fcnt_up'
    fcnt_down = 'fcnt_down'
    dev_class = 'dev_class'
    app_eui = 'app_eui'
    adr = 'adr'
    check_fcnt = 'check_fcnt'
    rx_window = 'rx_window'
    frequency = 'frequency'


class TXParams:
    RX1DRoffset = 'RX1DRoffset'
    RX2DataRate = 'RX2DataRate'
    RX2Frequency = 'RX2Frequency'
    RxDelay = 'RxDelay'