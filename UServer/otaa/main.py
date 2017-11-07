
import json
from binascii import hexlify
import requests
from gevent import Greenlet
from database.db1 import db1, Channel1
from database.db0 import db0
from userver.object.addr import AddrManger

from binascii import unhexlify
from base64 import b64decode
from datetime import datetime

from .objects.device import JoiningDev, Device, ActiveMode, db_session
from .log import logger, ConstLog
from config import HOST
import time
import calendar
from sqlalchemy import create_engine
from config import SQLALCHEMY_DATABASE_URI

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
engine = create_engine(SQLALCHEMY_DATABASE_URI)
appCache = {}


# class ListenJoinReqThreading(threading.Thread):
#     def __init__(self):
#         threading.Thread.__init__(self, daemon=True)


def process_join_request(data):
    global appCache
    error_msg = None
    try:
        app_eui = unhexlify(data['app_eui'])
        app_eui_str = data['app_eui']
        dev_eui = unhexlify(data['dev_eui'])
        device = db_session.query(Device).get(dev_eui)
        if device is None:
            error_msg = 'DEV:%s is not registered' % hexlify(dev_eui).decode()
            logger.error(ConstLog.join_req + error_msg)
            return
        elif device.app_eui != app_eui:
            error_msg = 'DEV:%s is already registered in other application'
            logger.error(ConstLog.join_req + 'DEV:%s belong to APP:%s, not APP:%s' % (hexlify(
                dev_eui).decode(), hexlify(device.app_eui).decode(), hexlify(app_eui).decode()))
            return
        addr = AddrManger.dis_dev_addr()
        try:
            join_dev = JoiningDev(app_eui, dev_eui, addr)
            join_dev.save()
        except Exception as error:
            error_msg = error
            logger.error(ConstLog.join_req + str(error_msg))
            return
        data['dev_addr'] = hexlify(join_dev.addr).decode()
        logger.info('OTAA DATA TO JOINSERVER: %s' % data)
        r = requests.post(url, data=json.dumps(data), headers=headers)
        try:
            data = r.json()
            logger.info(ConstLog.join_resp +
                        'GET MSG FROM JOIN SERVER %s' % data)
            if r.ok:
                accept_msg = data.get('accept_msg')
                if accept_msg is not None:
                    if app_eui_str in appCache.keys():
                        device.active(addr=join_dev.addr, dev_class='C', nwkskey=b64decode(
                            data['nwkskey']), appskey=b64decode(data['appskey']))
                    else:
                        device.active(addr=join_dev.addr, nwkskey=b64decode(
                            data['nwkskey']), appskey=b64decode(data['appskey']))
                    device.active_at = datetime.utcnow()
                    device.active_mode = ActiveMode.otaa
                    db_session.commit()
                    db1.publish(Channel1.join_accept_alarm +
                                hexlify(join_dev.dev_eui).decode(), accept_msg)
                    device.publish()
                    logger.info('[OTAA] device %s join success' %
                                hexlify(device.dev_eui).decode())
                    logger.info(ConstLog.publish + Channel1.join_accept_alarm +
                                hexlify(join_dev.dev_eui).decode() + ': %s' % accept_msg)
            else:
                error_msg = data.get('error')
                if error_msg is not None:
                    logger.error(ConstLog.join_resp + str(error_msg))
                    return
        except Exception as error:
            error_msg = error
            logger.error(ConstLog.join_resp + str(error_msg))
    except Exception as error:
        error_msg = error
        logger.error(
            '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!' + str(error_msg))
    finally:
        db_session.close()
        if error_msg:
            db0.publish(Channel1.join_error_alarm + hexlify(app_eui).decode(), message=json.dumps(
                {'dev_eui': hexlify(dev_eui).decode(), 'error': str(error_msg), 'ts': time.time()}))


def listen_join_request():
    ps = db1.pubsub()
    ps.subscribe(Channel1.join_req_alarm)
    while True:
        for item in ps.listen():
            logger.info(ConstLog.join_req + 'LISTEN MSG ' + str(item))
            if item['type'] == 'message':
                data = item['data'].decode()
                data = json.loads(data)
                thr = Greenlet(process_join_request, data)
                thr.run()


def fresh_cache():
    # global sockLocal
    # sockLocal = doConnect(host, port)
    # send_data(procSensor())
    while True:
        global appCache
        result = engine.execute("select * from app_default_class")
        tmpCache = {}
        for row in result:
            key = str(row['app_eui']).replace("-", "").lower()
            tmpCache[key] = row
        appCache = tmpCache
        time.sleep(6)
