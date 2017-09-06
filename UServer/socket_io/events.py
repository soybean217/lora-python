import threading
import time
from binascii import hexlify, unhexlify
from gevent import Greenlet, sleep

from flask import request
from flask_socketio import emit, disconnect

from .application import Application
from userver.object.message import ConstMsg, ConstCmd
from userver.object.message import MsgUp, MsgDn, Msg
from userver.object.que_down import QueDownDev, QueDownGroup
from utils.errors import PasswordError
from utils.log import logger, ConstLog
from utils.utils import display_hex
from . import socketio


thread_dict = {}


class Event:
    post_rx = 'post_rx'
    tx = 'tx'
    ack_tx = 'ack_tx'
    confirm_tx = 'confirm_tx'
    cache_query = 'cache_query'
    abp_req = 'abp_req'


class CMDError(Exception):
    def __init__(self, event, cmd):
        """
        :param event:
        :param cmd:
        :return:
        """
        self.event = event
        self.cmd = cmd

    def __str__(self):
        return 'Event %s has no CMD %s' % self.event, self.cmd


class WatchThreadThreading(Greenlet):
    def __init__(self):
        """
        :param app_eui: bytes
        :param request_sid:
        :return:
        """
        Greenlet.__init__(self)

    def run(self):
        global thread_dict
        while True:
            logger.info('thread_dict: len: ' + '%s' % len(thread_dict))
            for thread in thread_dict:
                logger.info('thread_dict: len: ' + '%s' % hexlify(thread.app_eui))
            sleep(30)


class ListenMsgThreading(Greenlet):
    def __init__(self, app_eui, request_sid):
        """
        :param app_eui: bytes
        :param request_sid:
        :return:
        """
        # threading.Thread.__init__(self, daemon=True)
        Greenlet.__init__(self)
        self.app_eui = app_eui
        self.request_sid = request_sid
        self.msg = Msg(self.app_eui)

    def stop(self):
        self.msg.stop_listen()
        logger.info(ConstLog.socketio + '%s Unsubscribed' % self.request_sid)

    def run(self):
        logger.info(ConstLog.socketio + 'ListenMsgThreading Started: ' + hexlify(self.app_eui).decode())

        ps = self.msg.listen_msg_alarm()
        for item in ps.listen():
            if item is not None:
                logger.info(ConstLog.socketio + 'LISTEN MSG ' + str(item))
                if item['type'] == 'message':
                    key = item['data'].decode()
                    key_split = key.split(':')
                    if key_split[0] == 'MSG_DOWN':
                        message = MsgDn.objects.get(key).confirm_tx()
                        logger.info(ConstLog.socketio + Event.confirm_tx + str(message))
                        socketio.emit(Event.confirm_tx, message, namespace='/test', room=self.request_sid)
                    elif key_split[0] == 'MSG_UP':
                        message = MsgUp.objects.get(key).post_rx()
                        logger.info(ConstLog.socketio + Event.post_rx + str(message))
                        socketio.emit(Event.post_rx, message, namespace='/test', room=self.request_sid)
                elif item['type'] == 'unsubscribe':
                    logger.info(ConstLog.socketio + '%s Unsubscribed' % self.request_sid)


@socketio.on('connect', namespace='/test')
def test_connect():
    try:
        app_eui = unhexlify(request.args.get('app_eui'))
        token = request.args.get('token')
        logger.info(ConstLog.socketio + 'CONNECTING app_eui: %s, token: %s' % (hexlify(app_eui).decode(), token))
        app = Application.query.get(app_eui)
        if app is not None:
            app.auth_token(token)
            emit('socket_connected')
            listen_msg_thread = ListenMsgThreading(app_eui, request.sid)
            listen_msg_thread.start()
            global thread_dict
            thread_dict[request.sid] = listen_msg_thread
            logger.info(ConstLog.socketio + 'CONNECTED %s' % request.sid)
        else:
            logger.info(ConstLog.socketio + 'CONNECT ERROR: APP%s is None' % app_eui)
    except PasswordError as e:
        logger.warning(ConstLog.socketio + 'CONECT ERROR ' + e.__str__())
        emit('connect_error', {'message': e.__str__()})
        disconnect()
    except KeyError:
        logger.warning(ConstLog.socketio + 'CONECT ERROR APP_EUI %s NOT FOUND' % hexlify(app_eui).decode())
        emit('connect_error', {'message': 'APP_EUI %s NOT FOUND' % hexlify(app_eui).decode()})
        disconnect()


@socketio.on('disconnect', namespace='/test')
def test_disconnect():
    global thread_dict
    listen_msg_thread = thread_dict.get(request.sid)
    if listen_msg_thread is not None:
        listen_msg_thread.stop()
        thread_dict.pop(request.sid)
    logger.info(ConstLog.socketio + 'DISCONNECTED ' + request.sid)


# @socketio.on('disconnect', namespace='/test')
# def test_disconnect():
#     print(threading.enumerate())
#     for thread in threading.enumerate():
#         if isinstance(thread, ListenMsgThreading):
#             if thread.request_sid == request.sid:
#                 thread.stop()
#                 logger.info(ConstLog.socketio + 'DISCONNECTED ' + request.sid)


@socketio.on('disconnect request', namespace='/test')
def disconnect_request():
    emit('socket_disconnect')
    logger.info(ConstLog.socketio + 'DISCONNECT REQUEST')
    disconnect()


@socketio.on('tx', namespace='/test')
def event_tx(message):
    logger.info(ConstLog.socketio + 'TX ' + str(message))
    try:
        cmd = message[ConstMsg.cmd]
        app_eui = unhexlify(request.args.get('app_eui'))
        eui = unhexlify(message[ConstMsg.eui])
        port = int(message[ConstMsg.port])
        data = message.get(ConstMsg.data)
        nonce = message.get('Nonce')
        cipher = False
        seqno = None
        if data is None:
            data = message.get(ConstMsg.encdata)
            if data is None:
                raise Exception('Data is None')
            cipher = True
            seqno = int(message[ConstMsg.seqno])
        if cmd == ConstCmd.tx:
            ack_tx_cmd = ConstCmd.txd
            que_down = QueDownDev(eui, app_eui)
            confirmed = message.get('confirmed')
            if confirmed is None:
                confirmed = False
            rx_window = message.get('rx_window')
            if rx_window is None:
                rx_window = 0
            else:
                rx_window = int(rx_window)
            que_down.push(port, unhexlify(data), cipher=cipher, seqno=seqno, confirmed=confirmed, rx_window=rx_window)
        elif cmd == ConstCmd.mtx:
            ack_tx_cmd = ConstCmd.mtxd
            que_down = QueDownGroup(app_eui, eui)
            que_down.push(port, unhexlify(data), cipher=cipher, seqno=seqno)
        else:
            ack_tx_cmd = 'cmd ERROR'
            raise Exception('cmd ERROR')

        emit('ack_tx', {ConstMsg.cmd: ack_tx_cmd,
                        ConstMsg.eui: message[ConstMsg.eui],
                        ConstMsg.success: True,
                        ConstMsg.data: data})
    except CMDError as error:
        logger.error(ConstLog.socketio + ' TX ' + str(error))
        emit('ack_tx', {ConstMsg.error: str(error)})
    except Exception as error:
        logger.error(ConstLog.socketio + ' TX ' + str(error))
        emit('ack_tx', {ConstMsg.cmd: cmd,
                        ConstMsg.eui: display_hex(message[ConstMsg.eui]),
                        ConstMsg.success: False,
                        ConstMsg.error: str(error)})


# ---------------------------------------------------WuHaorong
@socketio.on('cache_query', namespace='/test')##Kevin
def event_cache_query(message):
    app_eui = unhexlify(request.args.get('app_eui'))
    if message['cmd'] == ConstCmd.cq:
        filter = message.get('filter')
        if filter is not None:
            start_ts = filter.get(ConstMsg.start_ts, 0)
            end_ts = filter.get(ConstMsg.end_ts, int(time.time()))
            dev_eui = filter.get(ConstMsg.dev_eui)
        else:
            start_ts = 0
            end_ts = int(time.time())
            dev_eui = None
        page_num = message.get(ConstMsg.page_num, 1)
        per_page = message.get(ConstMsg.per_page, 100)
        msgs = MsgUp.objects.all(app_eui, dev_eui, start_ts, end_ts)
        cache = [msg.post_rx() for msg in msgs]
        total = len(cache)
        #return to client
        return_data = {  ConstMsg.cmd: ConstCmd.cq,
                         ConstMsg.filter: {ConstMsg.start_ts: start_ts,
                                           ConstMsg.end_ts: end_ts,
                                           ConstMsg.dev_eui: dev_eui},
                         ConstMsg.page_num: page_num,
                         ConstMsg.per_page: per_page,
                         ConstMsg.total: total,
                         ConstMsg.cache: cache}
        emit(Event.cache_query, return_data)


# @socketio.on('abp_req', namespace='/test')
# def event_abp_req(message):
#     #analyze message
#     try:
#         # print(message)
#         dev_eui = unhexlify(message[ConstMsg.dev_eui])
#         name = message.get(ConstMsg.name, '')
#         dev_addr = unhexlify(message[ConstMsg.dev_addr])
#         nwkskey = unhexlify(message[ConstMsg.nwkskey])
#         app_eui = unhexlify(request.args.get('app_eui'))
#         try:
#             #import dev
#             device = Device(dev_eui, dev_addr, app_eui, nwkskey, name=name)
#             device.save()
#             #return to client
#             return_data = {ConstMsg.cmd: Event.abp_req,
#                            ConstMsg.dev_eui: message[ConstMsg.dev_eui],
#                            ConstMsg.success: 1,
#                            }
#             emit(Event.abp_req, return_data)
#         except AssertionError as error:
#             return_data = {ConstMsg.cmd: Event.abp_req,
#                            ConstMsg.dev_eui: message[ConstMsg.dev_eui],
#                            ConstMsg.success: 0,
#                            ConstMsg.error: str(error)}
#             emit(Event.abp_req, return_data)
#             logger.error(ConstLog.socketio + Event.abp_req + str(error))
#         except KeyDuplicateError as error:
#             return_data = {ConstMsg.cmd: Event.abp_req,
#                            ConstMsg.dev_eui: message[ConstMsg.dev_eui],
#                            ConstMsg.success: 0,
#                            ConstMsg.error: str(error)}
#             emit(Event.abp_req, return_data)
#             logger.error(ConstLog.socketio + Event.abp_req + str(error))
#     except Exception as error:
#         return_data = {ConstMsg.cmd: Event.abp_req,
#                        ConstMsg.success: 0,
#                        ConstMsg.error: str(error)}
#         emit(Event.abp_req, return_data)
#         logger.error(ConstLog.socketio + Event.abp_req + str(error))
#
#
# @socketio.on('mac_cmd', namespace='/test')
# def event_mac_command(message):
#     logger.info(ConstLog.socketio + 'MAC_CMD ' + str(message))
#     try:
#         dev_eui = message['dev_eui']
#         mac_cmd = message['mac_cmd']
#         device = Device.objects.get(dev_eui)
#         if device is not None:
#             MACCmd(mac_cmd, dev_eui).push_into_que()
#             emit('mac_cmd', {'cmd': 'mac_cmd',
#                              'dev_eui': dev_eui,
#                              'success': 1, })
#         else:
#             emit('mac_cmd', {'cmd': 'mac_cmd',
#                             'dev_eui': dev_eui,
#                             'success': 0,
#                             'error': 'Not Imported Device'})
#     except KeyError as error:
#         emit('mac_cmd', {'cmd': 'mac_cmd',
#                          'success': 0,
#                          'error': str(error)})
#     except Exception as error:
#         logger.error(ConstLog.socketio + ' MAC_CMD ' +str(error))


# @socketio.on('add_group', namespace='/test')
# def event_add_group(message):
#     logger.info(ConstLog.socketio + 'GET ADD GROUP REQUEST ' + str(message))
#     app_eui = unhexlify(request.args.get('app_eui'))
#     try:
#         name = message['name']
#         group_addr = int.to_bytes(int.from_bytes(unhexlify(message['group_addr']), byteorder='big'), byteorder='little', length=4)
#         nwkskey = unhexlify(message['nwkskey'])
#         appskey = unhexlify(message.get('appskey',''))
#         try:
#             group = Group(app_eui, name, group_addr, nwkskey, appskey=appskey)
#             group.save()
#             emit('add_group', {'cmd':           'add_group',
#                                'group_addr':    message['group_addr'],
#                                'group_id':      hexlify(group.id).decode(),
#                                'success':       1})
#             logger.info(ConstLog.socketio + message['group_addr'] + ' import successfully.')
#         except AssertionError as error:
#             logger.error(ConstLog.socketio + ' ADD_GROUP ' +str(error))
#             emit('add_group', {'cmd':           'add_group',
#                                'group_addr':    message['group_addr'],
#                                'success':       0,
#                                'error':         str(error)})
#         except KeyDuplicateError as error:
#             logger.error(ConstLog.socketio + ' ADD_GROUP ' +str(error))
#             emit('add_group', {'cmd':       'add_group',
#                                'group_addr':    message['group_addr'],
#                                'success':   0,
#                                'error':     str(error)})
#     except KeyError as error:
#         logger.error(ConstLog.socketio + ' ADD_GROUP ' +str(error))
#         emit('add_group', {'cmd':       'add_group',
#                            'success':   0,
#                            'error':     str(error)})
#     except Exception as error:
#         logger.error(ConstLog.socketio + ' ADD_GROUP ' +str(error))
#
#
# @socketio.on('add_dev_into_group', namespace='/test')
# def event_add_dev_into_group(message):
#     logger.info(ConstLog.socketio + 'GET ADD DEV INTO GROUP REQUEST ' + str(message))
#     app_eui = unhexlify(request.args.get('app_eui'))
#     try:
#         group_id = unhexlify(message['group_id'])
#         dev_eui = unhexlify(message['dev_eui'])
#         try:
#             group = Group.objects.get(app_eui, group_id)
#             group.add_device(dev_eui)
#             emit('add_dev_into_group', {'cmd':  'add_dev_into_group',
#                                         'dev_eui':  message['dev_eui'],
#                                         'success':  1})
#         except KeyDuplicateError as error:
#             logger.error(ConstLog.socketio + ' ADD_DEV_INTO_GROUP ' +str(error))
#             emit('add_dev_into_group', {'cmd':       'add_dev_into_group',
#                                         'dev_eui':   message['dev_eui'],
#                                         'success':   0,
#                                         'error':     str(error)})
#         except AssertionError as error:
#             logger.error(ConstLog.socketio + ' ADD_DEV_INTO_GROUP ' +str(error))
#             emit('add_dev_into_group', {'cmd':       'add_dev_into_group',
#                                         'dev_eui':   message['dev_eui'],
#                                         'success':   0,
#                                         'error':     str(error)})
#     except KeyError as error:
#         logger.error(ConstLog.socketio + ' ADD_DEV_INTO_GROUP ' +str(error))
#         emit('add_dev_into_group', {'cmd':       'add_dev_into_group',
#                                     'success':   0,
#                                     'error':     str(error)})
#     except Exception as error:
#         logger.error(ConstLog.socketio + ' ADD_DEV_INTO_GROUP ' +str(error))
#
#
# @socketio.on('rm_dev_from_group', namespace='/test')
# def event_rm_dev_into_group(message):
#     logger.info(ConstLog.socketio + 'GET REMOVE DEV INTO GROUP REQUEST ' + str(message))
#     app_eui = unhexlify(request.args.get('app_eui'))
#     try:
#         group_id = unhexlify(message['group_id'])
#         dev_eui = unhexlify(message['dev_eui'])
#         try:
#             group = Group.objects.get(app_eui, group_id)
#             group.rem_device(dev_eui)
#             emit('rm_dev_into_group', {'cmd':   'rm_dev_from_group',
#                                        'dev_eui':   message['dev_eui'],
#                                        'success':   1,
#                                        })
#         except AssertionError as error:
#             logger.error(ConstLog.socketio + ' REMOVE_DEV_INTO_GROUP ' +str(error))
#             emit('rm_dev_into_group', {'cmd':       'rm_dev_into_group',
#                                        'dev_eui':   message['dev_eui'],
#                                        'success':   0,
#                                        'error':     str(error)})
#     except KeyError as error:
#         logger.error(ConstLog.socketio + ' REMOVE_DEV_INTO_GROUP ' +str(error))
#         emit('rm_dev_into_group', {'cmd':       'rm_dev_into_group',
#                                    'success':   0,
#                                    'error':     str(error)})
#     except Exception as error:
#         logger.error(ConstLog.socketio + ' REMOVE_DEV_INTO_GROUP ' +str(error))