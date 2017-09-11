#! /usr/bin/env python
#-*- coding:utf-8 -*-

import os
import sys
import time
import socket
# import crc16
from binascii import unhexlify
from binascii import hexlify
import crcmod
import codecs


def doConnect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((host, port))
    except:
        pass
    return sock

header = {}
# 地磁数据报文 0x20
# 主机状态报文 0x21
header['type'] = b'\x20'
header['host_code_machine_id'] = 3
# B 代表市场展示；D 代表销售订单；E 代表测试项目
header['host_code_sale_type'] = b'\x0d'
header['host_code_sale_year'] = 17
header['host_code_project_id'] = 1
sensorBody = {}
sensorBody['position_id'] = 1
sensorBody['sensor_state'] = 1
sensorBody['park_count'] = 1
sensorBody['voltage'] = 1
sensorBody['reserved_field'] = 0
heartbeatBody = {}
heartbeatBody['alarm'] = 0
heartbeatBody['voltage'] = 13000
heartbeatBody['reserved'] = 0


crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)


def procHeaderer():
    return header['host_code_machine_id'].to_bytes(4, byteorder='little') + header['host_code_project_id'].to_bytes(3, byteorder='little') + header['host_code_sale_year'].to_bytes(2, byteorder='big') + header['host_code_sale_type'] + int(round(time.time())).to_bytes(8, byteorder='little')


def procSensor():
    tmpHeader = b'\x20' + procHeaderer()
    tmpBody = heartbeatBody['alarm'].to_bytes(1, byteorder='little') + sensorBody['sensor_state'].to_bytes(
        4, byteorder='little') + sensorBody['park_count'].to_bytes(2, byteorder='little') + sensorBody['voltage'].to_bytes(1, byteorder='little') + sensorBody['reserved_field'].to_bytes(7, byteorder='little')
    crc = crc16(tmpHeader + tmpBody)
    return tmpHeader + tmpBody + crc.to_bytes(2, byteorder='big')


def procHeartbeat():
    tmpHeader = b'\x21' + procHeaderer()
    tmpBody = sensorBody['position_id'].to_bytes(1, byteorder='little') + heartbeatBody[
        'voltage'].to_bytes(2, byteorder='little') + heartbeatBody['reserved'].to_bytes(1, byteorder='big')
    crc = crc16(tmpHeader + tmpBody)
    # crc = crc16.crc16xmodem(tmpHeader)
    return tmpHeader + tmpBody + crc.to_bytes(2, byteorder='big')


def main():
    host, port = "testgeo.bolinparking.com", 12366
    sockLocal = doConnect(host, port)

    while True:
        try:
            msg = procHeartbeat()
            msg = procSensor()
            sockLocal.send(msg)
            print("send msg ok : ", len(msg))
            print("send msg ok : ", hexlify(msg).decode())
            recv = sockLocal.recv(1024)
            print("recv data :", recv)
            print("recv data :", hexlify(recv).decode())
        except socket.error:
            print("socket error,do reconnect ")
            time.sleep(3)
            sockLocal = doConnect(host, port)
        # except:
        #     print('other error occur ')
        #     time.sleep(3)
        time.sleep(1)

if __name__ == "__main__":
    main()
