import logging
import sys

# 创建一个logger
logger = logging.getLogger('mylogger')
logger.setLevel(logging.DEBUG)
# logger.makeRecord(exc_info=True)

# # 创建一个handler，用于写入日志文件
# fh = logging.FileHandler('test.log')
# fh.setLevel(logging.DEBUG)

# 再创建一个handler，用于输出到控制台
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.DEBUG)

# 定义handler的输出格式
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s %(filename)s %(funcName)s %(lineno)s - %(message)s')
# fh.setFormatter(formatter)
ch.setFormatter(formatter)

# 给logger添加handler
# logger.addHandler(fh)
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
    join_req = '[JOIN REQ]:'
    join_resp = '[JOIN_RESP]'
    join_success = '[JOIN SUCCESS]'
    publish = '[PUBLISH]: '
