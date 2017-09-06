import logging
import sys

# 创建一个logger
logger = logging.getLogger('mylogger')
logger.setLevel(logging.DEBUG)
# logger.makeRecord(exc_info=True)

# 创建一个handler，用于写入日志文件
fh = logging.FileHandler('test_address2gps.log')
# fh = logging.FileHandler('test.log')
fh.setLevel(logging.INFO)

# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)

# 定义handler的输出格式
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)

# 给logger添加handler
logger.addHandler(ch)

# def my_handler(type, value, tb):
#     print('HELOOOEIJOFJOSEJF')
#     logger.error("Uncaught exception: {0}".format(str(value)))
#
# # Install exception handler
#
# sys.excepthook = my_handler


class ConstLog:
    socketio = '[SOCKETIO]: '
    group = '[GROUP]: '
    gateway = '[GATEWAY]: '
    app = '[APP]: '
    device = '[DEVICE]: '
    class_c = '[Class C]: '
    multi = '[MULTI]: '
    mac_cmd = '[MAC_CMD]: '


class Resource:
    app = 'APP'
    gateway = 'GATEWAY'
    device = 'DEVICE'
    group = 'GROUP'
    trans_params = 'trans_params'


class Action:
    get = 'GET'
    post = 'POST'

    add = 'ADD'
    publish = 'PUBLISH'
    listen = 'LISTEN'


class Logger:
    @staticmethod
    def info(action='', resource='', id='', msg=''):
        logger.info('%s - %s - %s - %s' % (action, resource, id, msg))

    @staticmethod
    def error(action='', resource='', id='', msg=''):
        logger.error('%s - %s - %s - %s' % (action, resource, id, msg))

    @staticmethod
    def debug(action='', resource='', id='', msg=''):
        logger.debug('%s - %s - %s - %s' % (action, resource, id, msg))

    @staticmethod
    def warning(action='', resource='', id='', msg=''):
        logger.warning('%s - %s - %s - %s' % (action, resource, id, msg))
