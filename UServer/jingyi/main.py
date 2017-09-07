
import json
from binascii import hexlify
import requests
from gevent import Greenlet
from database.db1 import db1, Channel1
from database.db0 import db0
from database.db2 import db2
from userver.object.addr import AddrManger

from binascii import unhexlify
from base64 import b64decode
from datetime import datetime

from .objects.device import JoiningDev, Device, ActiveMode, db_session
from .log import logger, ConstLog
from config import HOST
import time
import calendar

"""
{'request_msg': '00a0000000000000a0a000000000000000bbe5c1b77f00',
 'dev_eui': '00000000000000a0',
 'dev_addr': '00000002',
 'app_eui': 'a0000000000000a0',
 'dl_settings': '00',
 'rx_delay': '01',
 'cf_list': '184f84e85684b85e84886684586e8400'}
"""

# url = 'http://183.230.40.231:6100/join?net_id=22&token=eXU7UoKsfBZ5dTtSgqx8Fg'

url = 'http://' + HOST + ':6100/join?net_id=22&token=eXU7UoKsfBZ5dTtSgqx8Fg'
headers = {'content-type': 'application/json'}


# class ListenJoinReqThreading(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self, daemon=True)


def doConnect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except:
        pass
    return sock


def listen_jingyi_request():
    host, port = "127.0.0.1", 12345
    # sockLocal = doConnect(host, port)
    ps = db2.pubsub()
    # ps.subscribe("up_alarm:9999939a00000000")
    ps.subscribe("up_alarm:1020304050607080")
    while True:
        for item in ps.listen():
            print(str(item))
            if item['type'] == 'message':
                print(str(item['data']))
                dataFromDev = db2.hgetall(item['data'])
                print(str(dataFromDev))
                print(str(dataFromDev['data']))
                # print(str(item['data'].decode()))
                # print(str(db2.get(item['data'].decode())))
                # thr = Greenlet(process_join_request, data)
                # thr.run()
