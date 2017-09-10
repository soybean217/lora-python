from database.db2 import db2
import time
from .log import logger
import crcmod
import socket
from binascii import hexlify
from gevent import Greenlet

host, port = "testgeo.bolinparking.com", 12366
# host, port = "127.0.0.1", 12345
sockLocal = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
header = {}
# 地磁数据报文 0x20
# 主机状态报文 0x21
header['type'] = b'\x20'
# 4099 地磁不存在 4100 业务处理未完成
header['host_code_machine_id'] = 666
# B 代表市场展示；D 代表销售订单；E 代表测试项目
header['host_code_sale_type'] = b'\x0d'
header['host_code_sale_year'] = b'\x17'
# test project id = 2
header['host_code_project_id'] = 2
sensorBody = {}
sensorBody['position_id'] = 0
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
    return header['host_code_machine_id'].to_bytes(4, byteorder='little') + header['host_code_project_id'].to_bytes(4, byteorder='little') + header['host_code_sale_year'] + header['host_code_sale_type'] + int(round(time.time())).to_bytes(8, byteorder='little')


def procHeartbeat():
    tmpHeader = b'\x21' + procHeaderer()
    tmpBody = heartbeatBody['alarm'].to_bytes(1, byteorder='little') + heartbeatBody[
        'voltage'].to_bytes(2, byteorder='little') + heartbeatBody['reserved'].to_bytes(1, byteorder='big')
    crc = crc16(tmpHeader + tmpBody)
    # crc = crc16.crc16xmodem(tmpHeader)
    return tmpHeader + tmpBody + crc.to_bytes(2, byteorder='big')


def procSensor():
    tmpHeader = b'\x20' + procHeaderer()
    tmpBody = sensorBody['position_id'].to_bytes(1, byteorder='little') + sensorBody['sensor_state'].to_bytes(
        4, byteorder='little') + sensorBody['park_count'].to_bytes(2, byteorder='little') + sensorBody['voltage'].to_bytes(1, byteorder='little') + sensorBody['reserved_field'].to_bytes(7, byteorder='little')
    crc = crc16(tmpHeader + tmpBody)
    return tmpHeader + tmpBody + crc.to_bytes(2, byteorder='big')


def doConnect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        logger.debug('begin connect to %s : %s', host, port)
        sock.connect((host, port))
    except:
        pass
    return sock


def heartbeat_jingyi():
    global sockLocal
    sockLocal = doConnect(host, port)
    # send_data(procSensor())
    while True:
        logger.debug("begin send heartbeat")
        thr = Greenlet(send_data, procHeartbeat())
        thr.run()
        # send_data(procHeartbeat())
        time.sleep(300)


def send_data(msg):
    global sockLocal
    try:
        sockLocal.send(msg)
        logger.debug("send msg ok : %s", len(msg))
        logger.debug("send msg ok : %s", hexlify(msg).decode())
        recv = sockLocal.recv(1024)
        logger.debug("recv data :%s", recv)
        logger.debug("recv data :%s", hexlify(recv).decode())
        logger.debug("recv data len :%s", len(recv))
    except socket.error:
        logger.error("socket error,do reconnect ... waiting timeout")
        time.sleep(3)
        sockLocal = doConnect(host, port)
        sockLocal.send(msg)
        logger.debug("resend msg len: %s", len(msg))
        logger.debug("resend msg: %s", hexlify(msg).decode())
        recv = sockLocal.recv(1024)
        logger.debug("recv data :%s", recv)
        logger.debug("recv data :%s", hexlify(recv).decode())


def proc_message(item):
    try:
        logger.debug(str(item['data']))
        sensorBody['position_id'] = get_position(
            str(item['data']).split(":")[1])
        logger.debug('get position with dev:%s', sensorBody['position_id'])
        if sensorBody['position_id'] > 0:
            dataFromDev = db2.hgetall(item['data'])
            logger.debug(str(dataFromDev))
            dataFrame = dataFromDev[b'data']
            logger.debug('len:%s', len(dataFrame))
            logger.debug(str(dataFrame))
            firstByte = int(dataFrame[0])
            frameType = (firstByte & 0b11110000) >> 4
            logger.debug('if weichuan frame type:%s', frameType)
            if (len(dataFrame) == 11 and frameType == 3) or (len(dataFrame) == 9 and frameType == 2) or (len(dataFrame) == 2 and frameType == 4):
                logger.debug('weichuan sensor')
                sensorBody['sensor_state'] = (
                    dataFrame[1] & 0b10000000) >> 7
                logger.debug('positionStatus:%s',
                             sensorBody['sensor_state'])
                voltage = (dataFrame[1] & 0b01111111)
                logger.debug('voltage:%s', voltage)
                sensorBody['voltage'] = voltage - 29
                logger.debug("begin send sensor data")
                send_data(procSensor())
                # send_data(procSensor())
                if len(dataFrame) > 2:
                    logger.debug('temperature:%d,%d' %
                                 (dataFrame[2], dataFrame[3]))
            elif firstByte == b'\xab' and len(dataFrame) == 5:
                logger.debug('tuobao sensor')
                sensorBody['sensor_state'] = (
                    dataFrame[2] & 0b10000000) >> 7
                logger.debug('positionStatus:%s',
                             sensorBody['sensor_state'])
                voltage = (dataFrame[2] & 0b01111111)
                logger.debug('voltage:%s', voltage)
                logger.debug('status:%s', dataFrame[1] & 0b00001111)
                sensorBody['voltage'] = voltage * 7 / 100
                send_data(procSensor())
    except Exception as error:
        error_msg = error
        logger.error(str(error_msg))


def get_position(dev_eui):
    if dev_eui == 'e702000010ffffff':
        return 96
    elif dev_eui == '9401000010ffffff':
        return 137
    elif dev_eui == '0003000010ffffff':
        return 136
    elif dev_eui == '7b03000010ffffff':
        return 135
    elif dev_eui == '8503000010ffffff':
        return 134
    elif dev_eui == 'a503000010ffffff':
        return 133
    elif dev_eui == '5602000010ffffff':
        return 132
    elif dev_eui == '7603000010ffffff':
        return 131
    elif dev_eui == '5803000010ffffff':
        return 130
    elif dev_eui == 'b702000010ffffff':
        return 129
    elif dev_eui == '1703000010ffffff':
        return 128
    elif dev_eui == '4b02000010ffffff':
        return 127
    elif dev_eui == 'd802000010ffffff':
        return 126
    elif dev_eui == '2702000010ffffff':
        return 125
    elif dev_eui == '9999939a99999998':
        return 102
    elif dev_eui == '9999939a9999999b':
        return 100
    elif dev_eui == '9999939a9999999c':
        return 98
    elif dev_eui == 'e702000010ffffff':
        return 96
    elif dev_eui == '7202000010ffffff':
        return 94
    elif dev_eui == 'e302000010ffffff':
        return 92
    elif dev_eui == 'ce03000010ffffff':
        return 90
    elif dev_eui == 'cd02000010ffffff':
        return 88
    elif dev_eui == 'a403000010ffffff':
        return 86
    elif dev_eui == '8d02000010ffffff':
        return 84
    elif dev_eui == '5902000010ffffff':
        return 82
    elif dev_eui == '7c03000010ffffff':
        return 80
    elif dev_eui == '8403000010ffffff':
        return 78
    elif dev_eui == '3303000010ffffff':
        return 76
    return 0


def listen_jingyi_request():
    global sensorBody
    # sockLocal = doConnect(host, port)
    ps = db2.pubsub()
    ps.subscribe("up_alarm:9999939a00000000")
    # ps.subscribe("up_alarm:1020304050607080")
    while True:
        for item in ps.listen():
            try:
                logger.debug(str(item))
                if item['type'] == 'message':
                    thr = Greenlet(proc_message, item)
                    thr.run()
            except Exception as error:
                error_msg = error
                logger.error(str(error_msg))
