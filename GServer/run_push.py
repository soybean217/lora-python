# Copyright (c) 2012 Denis Bilenko. See LICENSE for details.
"""A simple UDP server.
For every message received, it sends a reply back.
You can use udp_client.py to send a message.
"""
from gevent.greenlet import Greenlet
from gevent.server import DatagramServer

from binascii import hexlify
from msg_read import read_push_data
from msg_write import write_push_ack
from object.gateway import Gateway
from datetime import datetime
from const import Const
from gevent import monkey; monkey.patch_socket()
import gevent
from utils.log import Logger, IDType, Action
from utils.timing_log import timing
import json
from config import HOST
g_token = {}
import time


# include recv uplink from gateway and send class A msg
class PushServer(DatagramServer):
    def handle(self, data, address):
        t0 = time.time()
        protocol_version = data[0]
        token = data[1:3]
        data_type = data[3]
        gateway_mac_addr = data[4:12]
        gateway = Gateway.objects.get(gateway_mac_addr)
        if gateway is not None:
            p_token = g_token.get(gateway.mac_addr)
            g_token[gateway.mac_addr] = token
            gateway.set_time(time.time())
            if data_type == Const.PUSH_DATA_IDENTIFIER:
                try:
                    datagram = json.loads(data[12:].decode())
                except Exception as error:
                    Logger.error(msg='%s' % error, type=IDType.gateway, action=Action.push_data, id='%s' % hexlify(gateway.mac_addr).decode())
                    return
                push_ack = write_push_ack(token, protocol_version)
                self.socket.sendto(push_ack, address)
                t1 = time.time()
                Logger.info(msg='%s' % push_ack, type=IDType.gateway, action=Action.push_ack, id='%s' % hexlify(gateway.mac_addr).decode())
                if p_token != token:
                    Logger.info(msg='NEW: %s ' % data, type=IDType.gateway, action=Action.push_data, id='%s' % hexlify(gateway.mac_addr).decode())
                    read_push_data(datagram, gateway, t0, t1)
                else:
                    Logger.info(msg='UDP_RETRANSMISSION: %s' % data, type=IDType.gateway, action=Action.push_data, id='%s' % hexlify(gateway.mac_addr).decode())
            else:
                Logger.error(msg='Get Unknow Data_type: %s' % data_type, type=IDType.gateway, action=Action.got, id='%s' % hexlify(gateway.mac_addr).decode())
        else:
            Logger.error(msg='Not Imported', type=IDType.gateway, action=Action.pull_ack, id='%s' % hexlify(gateway_mac_addr).decode())


def serve(server):
    print('[GServer] begin to work!')
    server.serve_forever()


if __name__ == '__main__':
    push_server = PushServer((9000))
    print('start serve on %s:%s' % (HOST, 9000))
    gevent.joinall([
        gevent.spawn(serve, push_server),
    ])