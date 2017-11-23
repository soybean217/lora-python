import logging
import sys
# 创建一个logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# 创建一个handler，用于写入日志文件
fh = logging.FileHandler('test.log')
fh.setLevel(logging.DEBUG)

# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# 定义handler的输出格式
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s %(funcName)s %(lineno)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 给logger添加handler
logger.addHandler(fh)
logger.addHandler(ch)


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.error("Uncaught exception", exc_info=(
        exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception


class Logger:

    @staticmethod
    def info(action='', type='', id='', msg=''):
        logger.info('%s - %s - %s - %s' % (action, type, id, msg))

    @staticmethod
    def error(action='', type='', id='', msg=''):
        logger.error('%s - %s - %s - %s' % (action, type, id, msg))

    @staticmethod
    def debug(action='', type='', id='', msg=''):
        logger.debug('%s - %s - %s - %s' % (action, type, id, msg))

    @staticmethod
    def warning(action='', type='', id='', msg=''):
        logger.warning('%s - %s - %s - %s' % (action, type, id, msg))


class IDType:
    gateway = 'GATEWAY'
    app = 'APP'
    device = 'DEV'
    group = 'GROUP'
    pkg = 'PKG'
    ip_addr = 'IP_ADDR'
    sub = 'SUB'
    dev_addr = 'DEVADDR'
    dev_info = 'DEV_INFO'
    dev_nonce = 'DEV_NONCE'
    pull_info = 'PULL_INFO'
    token = 'TOKEN'


class Action:
    class_c = 'CLASS_C'
    class_b = 'CLASS_B'
    multi = 'MULTI'
    rxpk = 'RXPK'
    rx1 = 'RX_1'
    pull = 'PULL'
    push = 'PUSH'
    resend = 'RESEND'

    mic = 'MIC'

    push_data = 'PUSH_DATA'
    push_ack = 'PUSH_ACK'
    pull_data = 'PULL_DATA'
    pull_ack = 'PULL_ACK'
    pull_resp = 'PULL_RESP'
    tx_ack = 'TX_ACK'

    got = 'GOT'

    otaa = 'OTAA'

    data_up = 'DATA_UP'
    proprietary = 'PROPRIETARY'

    uplink = 'UPLINK'
    downlink = 'DOWNLINK'

    sem = 'SEM'

    lock = 'LOCK'

    mac_cmd_get = 'MAC_CMD GET'
    mac_cmd_send = 'MAC_CMD SEND'

    object = 'OBJECT'

    adr = 'ADR'

    gateway = 'GATEWAY'


class ConstLog:
    get = '[GET]: '
    send = '[SEND]: '
    otaa = '[OTAA]: '
    rxpk = '[RXPK]: '
    adr = '[ADR]: '
    txpk = '[TXPK]: '
    txpk_multi = '[TXPK_MULTI]: '
    multi = '[MULTI]: '
    class_a = '[CLASS A]: '
    class_b = 'CLASS_B'
    class_c = '[CLASS C]: '
    publish = '[PUBLISH]: '
    mac_cmd = '[MAC CMD]'
    mac_cmd_answer = '[MAC CMD ANSWER]'
    newch = '[NEWChannel]'
    rxtime = '[RXTiming]'
    device = '[DEVICE]: '
    gateway = '[GATEWAY]: '
    application = '[APP]: '
    rx1 = '[RX1]: '
