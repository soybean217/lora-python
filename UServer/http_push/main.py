from gevent import monkey; monkey.patch_all()

from binascii import unhexlify
from gevent import Greenlet
from .application import sess, HttpPush
from userver.object.message import MsgUp
from utils.log import logger, ConstLog
import requests
from database.db0 import db0, Channel


def listen_msg():
    logger.info(ConstLog.socketio + 'ListenMsgThreading Started')
    ps = db0.pubsub()
    ps.psubscribe(Channel.msg_alarm + '*')
    for item in ps.listen():
        if item is not None:
            logger.info('LISTEN MSG ' + str(item))
            if item['type'] == 'pmessage':
                thr = Greenlet(run=handle_msg, msg_key=item['data'].decode())
                thr.start()


def handle_msg(msg_key):
    try:
        key_split = msg_key.split(':')
        if key_split[0] == 'MSG_UP':
            app_eui = unhexlify(key_split[1])
            http_push = sess.query(HttpPush).get(app_eui)
            if http_push and http_push.url:
                message = MsgUp.objects.get(msg_key).post_rx()
                logger.info('Posting to url: %s msg:%s' % (http_push.url, message))
                try:
                    a = requests.post(http_push.url, json=message)
                    logger.info('Success Post: %s' % a)
                except Exception as e:
                    logger.error('Failure Post: Error : %s' % e)
    except Exception as error:
        sess.remove()
        logger.error('Error : %s' % error)
