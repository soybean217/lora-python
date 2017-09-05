# Copyright (c) 2012 Denis Bilenko. See LICENSE for details.
"""A simple UDP server.
For every message received, it sends a reply back.
You can use udp_client.py to send a message.
"""
import json
from gevent.server import DatagramServer
from object.gateway import Gateway
from const import Const
from gevent import monkey
import gevent
from utils.log import logger, ConstLog
from binascii import hexlify
from object.config import Config
from utils.utils import pack_longitude, pack_latitude
from object.gateway import Platform
monkey.patch_socket()

latest_ver = {Platform.RaspBerryPi: "0.1.1",
              Platform.LinkLabs: "0.1.1",
              Platform.RaspBerryPi3: "0.1.1"}


def ver_small(platform, fw_ver):
    fw_ver = fw_ver.split('.')
    lat_ver = latest_ver[platform].split('.')
    if fw_ver[0] < lat_ver[0]:
        return True
    elif fw_ver[0] > lat_ver[0]:
        return False
    else:
        if fw_ver[1] < lat_ver[1]:
            return True
        elif fw_ver[1] > lat_ver[1]:
            return False
        else:
            if fw_ver[2] < lat_ver[2]:
                return True
            else:
                return False


def addition_fw_ver(gateway_id):
    addition_fw_ver = open("configs/addition_fw_ver.json", 'r')
    file = json.loads(addition_fw_ver.read()).get(hexlify(gateway_id).decode())
    addition_fw_ver.close()
    return file


class EchoServer(DatagramServer):
    def handle(self, data, address):
        logger.info(ConstLog.rx + '%s: got %r' % (address[0], data))
        protocol_version = data[0]
        token = data[1:3]
        data_type = data[3:4]
        id = data[4:12]
        # send PUSH_ACK packet to acknowledge immediately all the PUSH_DATA packets received
        len_data = len(data)
        # if bytes([protocol_version]) == Const.PROTOCOL_VERSION_1 and data_type == Const.CONFIG_IDENTIFIER:
        if data_type == Const.CONFIG_IDENTIFIER:
            gateway = Gateway.objects.get(id)
            if gateway is not None:
                if len_data > 12 and data[12] == 123 and data[len_data-1] == 125:
                    request_data = data[12:].decode().replace(",}", "}")
                    if len(request_data) > 0:
                        request_data = json.loads(request_data)
                        fw_ver = request_data.get("fw_ver")
                        if not fw_ver:
                            fw_ver = request_data.get("software_ver")
                        if fw_ver:
                            fw_ver_split = fw_ver.split('.')
                            expect_ver = addition_fw_ver(gateway.id)
                            if len(fw_ver_split) == 3 and((expect_ver and fw_ver != expect_ver) or (not expect_ver and (fw_ver == '255.255.255' or ver_small(gateway.platform, fw_ver)))):
                                conf = Config.get_conf('update', protocol_version=protocol_version)
                                if expect_ver:
                                    conf["file_path"] = 'lora-ftp/niot_pkt_fwd-' + gateway.platform.value + '-' + expect_ver
                                else:
                                    conf["file_path"] = 'lora-ftp/niot_pkt_fwd-' + gateway.platform.value
                                head = int.to_bytes(protocol_version, length=1, byteorder='big') + token + Const.CONIG_UPG
                                payload = json.dumps(conf).encode()
                            elif len(fw_ver_split) == 4 and fw_ver not in Const.LAST_FW_VER_SET:
                                conf = Config.get_conf('update', protocol_version=protocol_version)
                                if expect_ver:
                                    # conf["file_path"] = Const.LAST_FW_VER_PATH[fw_ver_split[0]] + expect_ver + '/' +\
                                    #                     Const.LAST_FW_VER_NAME
                                    file_dir = Const.LAST_FW_VER_PATH[fw_ver_split[0]] + expect_ver + '/'
                                    conf["file_path"] = file_dir  + Const.LAST_FW_VER_NAME
                                    conf["md_path"] = file_dir + Const.LAST_FW_VER_NAME + '.md'
                                    conf["version"] = fw_ver_split[0] + '.' + expect_ver
                                else:
                                    # conf["file_path"] = Const.LAST_FW_VER_PATH[fw_ver_split[0]] + \
                                    #                     Const.LAST_FW_VER_DEFAULT[fw_ver_split[0]] + '/' +\
                                    #                     Const.LAST_FW_VER_NAME
                                    file_dir = Const.LAST_FW_VER_PATH[fw_ver_split[0]] + Const.LAST_FW_VER_DEFAULT[fw_ver_split[0]] + '/'
                                    conf["file_path"] = file_dir + Const.LAST_FW_VER_NAME
                                    conf["md_path"] = file_dir + Const.LAST_FW_VER_NAME + '.md'
                                    conf["version"] = fw_ver_split[0] + '.' + Const.LAST_FW_VER_DEFAULT[fw_ver_split[0]]
                                head = int.to_bytes(protocol_version, length=1,
                                                    byteorder='big') + token + Const.CONIG_UPG
                                payload = json.dumps(conf).encode()
                            else:
                                conf = Config.get_conf(gateway.freq_plan, protocol_version=protocol_version)
                                gateway_conf = conf["gateway_conf"]
                                gateway_conf["ref_latitude"] = pack_latitude(gateway.location.lat)
                                gateway_conf["ref_longitude"] = pack_longitude(gateway.location.lng)
                                gateway_conf["ref_altitude"] = gateway.location.alt
                                head = int.to_bytes(protocol_version, length=1, byteorder='big') + token + Const.CONFIG_RESP_IDENTIFIER
                                payload = json.dumps(conf).encode()
                            # self.socket.sendto(send_data, address)
                            self.sender(head, payload, address, protocol_version)
                        else:
                            logger.info(ConstLog.tx + 'Lack information of fw_ver')
            else:
                logger.info(ConstLog.rx + 'Gateway %s is not imported' % hexlify(id).decode())

    def sender(self, head, payload, address, protocol):
        data_type = head[len(head) - 1:]
        # if protocol == Const.PROTOCOL_FRAG_VERSION_2 and data_type == Const.CONFIG_RESP_IDENTIFIER:
        if (protocol in Const.PROTOCOL_FRAG_SET) and data_type == Const.CONFIG_RESP_IDENTIFIER:
            start_size = 0
            # data_length = len(head + payload)
            frag_payload_size = 1400 - len(head) - 1
            payload_length = len(payload)
            count = 1
            while payload_length > start_size:
                end_size = start_size + frag_payload_size
                if payload_length > end_size:
                    data = head + int.to_bytes(count, length=1, byteorder='big') + payload[start_size:end_size]
                    self.socket.sendto(data, address)
                    logger.info(ConstLog.tx + 'Send (MultiFrag:%s) %s to address: %s:%d' %
                                (count, str(data), address[0], address[1]))
                else:
                    data = head + int.to_bytes(count, length=1, byteorder='big') + payload[start_size:]
                    self.socket.sendto(data, address)
                    logger.info(ConstLog.tx + 'Send (MultiFrag:%s) %s to address: %s:%d' %
                                (count, str(data), address[0], address[1]))
                start_size = end_size
                count += 1
            # logger.info(ConstLog.tx + 'Send MultiFrag %s to address: %s:%d' % ((data,) + address))
        else:
            data = head + payload
            self.socket.sendto(data, address)
            logger.info(ConstLog.tx + 'Send %s to address: %s:%d' % ((data,) + address))


def server(a):
    logger.info('[GCServer] begin to work!')
    a.serve_forever()

# ip = "127.0.0.1"
ip = "183.230.40.231"

if __name__ == '__main__':
    a = EchoServer((7200))
    gevent.joinall([
        gevent.spawn(server, a), ])
