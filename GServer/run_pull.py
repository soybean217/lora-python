# Copyright (c) 2012 Denis Bilenko. See LICENSE for details.
"""A simple UDP server.
For every message received, it sends a reply back.
You can use udp_client.py to send a message.
"""
from gevent.greenlet import Greenlet
from gevent.server import DatagramServer

from object import Resend
from binascii import hexlify
from msg_write import write_pull_ack, write_pull_resp, write_pull_resp_multi, get_random_token
from msg_write import write_push_ack
from msg_read import read_push_data
from object.gateway import Gateway, PullInfo
from object.device import Device, ClassType
from datetime import datetime
from const import Const
from object.message import MsgDn
from object.group import Group
from otaa import write_join_accept_data
from gevent import monkey
monkey.patch_socket()
from gevent import sleep
import gevent
import time
import json
from binascii import unhexlify
from utils.log import Logger, IDType, Action
from utils.timing_log import timing
from utils.db0 import db0, Channel0, ConstDB0
from utils.db1 import db1, Channel1
from utils.db6 import db6, CHANNEL_TX_ACK
from config import HOST
g_token = {}
import sys


class PullServer(DatagramServer):

    def handle(self, data, address):
        protocol_version = data[0]
        token = data[1:3]
        data_type = data[3]
        if data_type == Const.TX_ACK_IDENTIFIER:
            db6.publish(CHANNEL_TX_ACK, token)
            Logger.info(action=Action.tx_ack, type=IDType.token, id=token,
                        msg='publish db6 %s: %s' % (CHANNEL_TX_ACK, token))
            return
        gateway_mac_addr = data[4:12]
        gateway = Gateway.objects.get(gateway_mac_addr)
        assert protocol_version == 1 or protocol_version == 2, 'PROTOCOL_VERSION ERROR, GOT: %s' % protocol_version
        if gateway is not None:
            p_token = g_token.get(gateway.mac_addr)
            g_token[gateway.mac_addr] = token
            gateway.set_time(time.time())
            if data_type == Const.PULL_DATA_IDENTIFIER:
                gateway.request2niot_platform()  # add to make request to
                # niot platform.
                restart = gateway.pop_restart()
                pull_ack = write_pull_ack(
                    protocol_version, token, gateway.disable, restart)
                self.socket.sendto(pull_ack, address)
                Logger.info(msg='%s' % pull_ack, type=IDType.ip_addr,
                            action=Action.pull_ack, id=address)
                if p_token != token:
                    Logger.info(msg='NEW: %s' % data, type=IDType.gateway,
                                action=Action.pull_data, id='%s' % hexlify(gateway.mac_addr).decode())
                    pull_info = PullInfo(
                        gateway.mac_addr, ip_addr=address, prot_ver=protocol_version)
                    pull_info.save()
                else:
                    Logger.info(msg='UDP_RETRANSMISSION: %s' % data, type=IDType.gateway,
                                action=Action.pull_data, id='%s' % hexlify(gateway.mac_addr).decode())
            #------------------ deprecated ------------------------#
            elif data_type == Const.PUSH_DATA_IDENTIFIER:
                try:
                    datagram = json.loads(data[12:].decode())
                except Exception as error:
                    Logger.error(msg='%s' % error, type=IDType.gateway,
                                 action=Action.push_data, id='%s' % hexlify(gateway.mac_addr).decode())
                    return
                push_ack = write_push_ack(token, protocol_version)
                self.socket.sendto(push_ack, address)
                Logger.info(msg='%s' % push_ack, type=IDType.gateway,
                            action=Action.push_ack, id='%s' % hexlify(gateway.mac_addr).decode())
                if p_token != token:
                    Logger.info(msg='NEW: %s' % data, type=IDType.gateway,
                                action=Action.push_data, id='%s' % hexlify(gateway.mac_addr).decode())
                    read_push_data(datagram, gateway)
                else:
                    Logger.info(msg='UDP_RETRANSMISSION %s' % data, type=IDType.gateway,
                                action=Action.push_data, id='%s' % hexlify(gateway.mac_addr).decode())
            #------------------- deprecated ------------------------#
            else:
                Logger.error(msg='Get Unknow Data_type: %s' % data_type, type=IDType.gateway,
                             action=Action.got, id='%s' % hexlify(gateway.mac_addr).decode())
        else:
            Logger.error(msg='Not Imported', type=IDType.gateway,
                         action=Action.pull_ack, id='%s' % hexlify(gateway_mac_addr).decode())


class ReSender(Greenlet):

    def __init__(self, pull_info, packet, server):
        Greenlet.__init__(self)
        self.ps = db6.pubsub()
        self.server = server
        self.packet = packet
        self.pull_info = pull_info
        self.token = packet[1:3]

    def _run(self):
        self.ps.subscribe(CHANNEL_TX_ACK)
        for i in range(0, 3):
            start = time.time()
            while time.time() - start < 0.1:
                sleep(0.05)
                for item in self.ps.listen():
                    Logger.debug(action=Action.resend, type=IDType.ip_addr,
                                 id=self.pull_info.ip_addr, msg='Get Publish TX, %s' % item)
                    # item = self.ps.get_message(timeout=0.05)
                    if item is not None and item['data'] == self.token:
                        Logger.info(action=Action.resend, type=IDType.ip_addr,
                                    id=self.pull_info.ip_addr, msg='Get Publish TX, %s' % item)
                        # return
                        continue
            self.server.sendto(self.packet, self.pull_info.ip_addr)
            Logger.info(action=Action.resend, type=IDType.ip_addr,
                        id=self.pull_info.ip_addr, msg='Resend data %s : %s' % (i, self.packet))
        Logger.error(action=Action.resend, type=IDType.gateway, id=self.pull_info.ip_addr,
                     msg='No TX_ACK got, PULL_RESP may not received by gateway')
        self.ps.unsubscribe()


class Sender(Greenlet):

    def __init__(self, dev_eui, server, rx_window, *args):
        Greenlet.__init__(self)
        self.server = server
        self.dev_eui = dev_eui
        self.rx_window = rx_window
        self.args = list(args)

    def run(self):
        device = Device.objects.get(self.dev_eui)
        if device.dev_class == ClassType.a or (device.dev_class == ClassType.c and self.rx_window == 1):
            send_info = write_pull_resp(device, rx_window=self.rx_window)
            if send_info is not None:
                send_data = send_info[0]
                fcnt = send_info[1]
                pull_info = send_info[2]
                self.server.socket.sendto(send_data, pull_info.ip_addr)
                t1 = time.time()
                self.args.append(t1)
                self.args.reverse()
                timing.info(msg='PULL_RESP: DEV:%s, TIME:%s' %
                            (hexlify(device.dev_eui).decode(), self.args))
                Logger.info(msg='RX1Sender %s' % send_data, action=Action.pull_resp,
                            type=IDType.ip_addr, id='%s:%d' % pull_info.ip_addr)
                if pull_info.prot_ver == 2:
                    resend = ReSender(pull_info, send_data, self.server)
                    resend.start()
                # msg = MsgDn(category=ConstDB0.dev, eui=hexlify(device.dev_eui).decode(), ts=int(time.time()), fcnt=fcnt)
                # msg.save()
        else:
            while device.que_down.len() != 0 or Resend(device.dev_eui).check_exist():
                send_data, fcnt, pull_info = write_pull_resp(
                    device, rx_window=self.rx_window)
                if send_data is not None:
                    self.server.socket.sendto(send_data, pull_info.ip_addr)
                    Logger.info(msg='CLASS_B Sender %s' % send_data, action=Action.pull_resp,
                                type=IDType.ip_addr, id='%s:%d' % pull_info.ip_addr)
                    if pull_info.prot_ver == 2:
                        resend = ReSender(pull_info, send_data, self.server)
                        resend.start()
                gevent.sleep(3)


def rx_1(server):
    ps = db0.pubsub()
    ps.subscribe(Channel0.rx1_alarm)
    while True:
        for item in ps.listen():
            Logger.info(msg='PS Listen %s' %
                        item, type=IDType.sub, action=Action.rx1)
            if item['type'] == 'message':
                t0 = time.time()
                sender = Sender(item['data'], server, 1, t0)
                sender.start()


def class_c(server):
    ps = db0.pubsub()
    ps.subscribe(Channel0.que_down_alarm_c)
    while True:
        for item in ps.listen():
            Logger.info(msg='PS Listen %s' %
                        item, type=IDType.sub, action=Action.class_c)
            if item['type'] == 'message':
                dev_eui = unhexlify(item['data'].decode().split(':')[1])
                # sender = ClassCSender(item['data'], server)
                sender = Sender(dev_eui, server, rx_window=2)
                sender.start()


def class_b(server):
    ps = db0.pubsub()
    ps.subscribe(Channel0.que_down_alarm_b)
    while True:
        for item in ps.listen():
            Logger.info(msg='PS Listen %s' %
                        item, type=IDType.sub, action=Action.class_b)
            if item['type'] == 'message':
                dev_eui = unhexlify(item['data'].decode().split(':')[1])
                # sender = ClassBSender(item['data'], server)
                sender = Sender(dev_eui, server=server, rx_window=0)
                sender.start()
            gevent.sleep(1)


def otaa(server):
    ps = db1.pubsub()
    ps.psubscribe(Channel1.join_accept_alarm + '*')
    while True:
        for item in ps.listen():
            Logger.info(msg='PS Listen %s' %
                        item, type=IDType.sub, action=Action.otaa)
            if item['type'] == 'pmessage':
                sender = OTAASender(item, server=server)
                sender.start()


class OTAASender(Greenlet):

    def __init__(self, item, server):
        Greenlet.__init__(self)
        dev_eui = unhexlify(item['channel'].decode().replace(
            Channel1.join_accept_alarm, ''))
        accept = item['data'].decode()
        self.server = server
        self.dev_eui = dev_eui
        self.data = accept

    def _run(self):
        result = write_join_accept_data(self.dev_eui, self.data)
        if not result:
            Logger.error(action=Action.otaa,
                         msg='No packet, pull_info return!!!')
            return
        packet = result[0]
        pull_info = result[1]
        if pull_info.prot_ver == 2:
            resend = ReSender(pull_info, packet, self.server)
            resend.start()
        self.server.sendto(packet, pull_info.ip_addr)
        Logger.info(action=Action.otaa, type=IDType.ip_addr, id='%s:%d' %
                    pull_info.ip_addr, msg='SENT JOIN ACCEPT %s' % packet)


def group(server):
    ps = db0.pubsub()
    ps.subscribe(Channel0.que_down_alarm_multi)
    Logger.info(msg='Listen IN GROUP', type=IDType.sub, action=Action.multi)
    while True:
        for item in ps.listen():
            Logger.info(msg='PS Listen %s' %
                        item, type=IDType.sub, action=Action.multi)
            if item['type'] == 'message':
                key_split = item['data'].decode().split(':')
                group = Group.objects.get(unhexlify(key_split[1]))
                send_packet_info = write_pull_resp_multi(group)
                if send_packet_info is not None:
                    send_packets = send_packet_info['packet']
                    pull_info_set = send_packet_info['pull_info_set']
                    fcnt = send_packet_info['fcnt']
                    for pull_info in pull_info_set:
                        for send_packet in send_packets:
                            send_packet = bytes([pull_info.prot_ver]) + get_random_token(
                            ) + Const.PULL_RESP_IDENTIFIER + json.dumps({'txpk': send_packet}).encode()
                            server.socket.sendto(
                                send_packet, pull_info.ip_addr)
                            Logger.info(msg='%s' % send_packet, action=Action.pull_resp,
                                        type=IDType.ip_addr, id='%s:%d' % pull_info.ip_addr)
                            # msg = MsgDn(category=ConstDB0.group, ts=int(time.time()), fcnt=fcnt, gateways=pull_info.mac_addr,
                            #             eui=hexlify(group.app.app_eui).decode() + ':' + hexlify(group.id).decode())
                            # msg.save()


# class ClassCSender(Greenlet):
#     def __init__(self, msg, server):
#         Greenlet.__init__(self)
#         self.server = server
#         self.msg = msg
#
#     def _run(self):
#         key_split = self.msg.decode().split(':')
#         dev_eui = key_split[1]
#         device = Device.objects.get(unhexlify(dev_eui))
#         while device.que_down.len() != 0 or Resend(device.dev_eui).check_exist():
#             send_info = write_pull_resp(device, rx_window=2)
#             if send_info is not None:
#                 send_data = send_info[0]
#                 fcnt = send_info[1]
#                 pull_info = send_info[2]
#                 self.server.socket.sendto(send_data, pull_info.ip_addr)
#                 # msg = MsgDn(category=ConstDB0.dev, eui=dev_eui, ts=int(time.time()), fcnt=fcnt)
#                 # msg.save()
#                 Logger.info(msg='ClassCSender %s' % send_data, action=Action.pull_resp, type=IDType.ip_addr, id='%s:%d' % pull_info.ip_addr)
#             gevent.sleep(3)
#
#
# class ClassBSender(Greenlet):
#     def __init__(self, msg, server):
#         Greenlet.__init__(self)
#         self.server = server
#         self.msg = msg
#
#     def _run(self):
#         key_split = self.msg.decode().split(':')
#         dev_eui = key_split[1]
#         device = Device.objects.get(unhexlify(dev_eui))
#         while device.que_down.len() != 0 or Resend(device.dev_eui).check_exist():
#             send_data, fcnt, pull_info = write_pull_resp(device, rx_window=0)
#             if send_data is not None:
#                 self.server.socket.sendto(send_data, pull_info.ip_addr)
#                 # msg = MsgDn(category=ConstDB0.dev, eui=dev_eui, ts=int(time.time()), fcnt=fcnt)
#                 # msg.save()
#                 Logger.info(msg='ClassBSender %s' % send_data, action=Action.pull_resp, type=IDType.ip_addr, id='%s:%d' % pull_info.ip_addr)


def serve(server):
    print('[GServer] begin to work!')
    server.serve_forever()


def handle_uncaught_except(exctype, value, traceback):
    print('??????????????????????')
    print(exctype, value, traceback)


if __name__ == '__main__':
    pull_server = PullServer((9200))
    print('start serve on %s:%s' % (HOST, 9200))

    gevent.joinall([
        gevent.spawn(serve, pull_server),
        gevent.spawn(class_c, pull_server),
        gevent.spawn(group, pull_server),
        gevent.spawn(rx_1, pull_server),
        gevent.spawn(class_b, pull_server),
        gevent.spawn(otaa, pull_server)
    ])
