from database.db2 import db2
import time
from .log import logger
import crcmod
import socket
from binascii import hexlify
from gevent import Greenlet

# host, port = "testgeo.bolinparking.com", 12366
host, port = "fsgeo.bolinparking.com", 16801
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
reserved_field = 0
heartbeatBody = {}
heartbeatBody['alarm'] = 0
heartbeatBody['voltage'] = 13000
heartbeatBody['reserved'] = 0
dataPositionGlobal = {}

crc16 = crcmod.mkCrcFun(0x18005, rev=True, initCrc=0xFFFF, xorOut=0x0000)


def procHeaderer():
    return header['host_code_machine_id'].to_bytes(4, byteorder='little') + header['host_code_project_id'].to_bytes(4, byteorder='little') + header['host_code_sale_year'] + header['host_code_sale_type'] + int(round(time.time())).to_bytes(8, byteorder='little')


def procSensorHeaderer(sensor):
    return sensor['host_code_machine_id'].to_bytes(4, byteorder='little') + header['host_code_project_id'].to_bytes(4, byteorder='little') + header['host_code_sale_year'] + header['host_code_sale_type'] + int(round(time.time())).to_bytes(8, byteorder='little')


def procHeartbeat():
    tmpHeader = b'\x21' + procHeaderer()
    tmpBody = heartbeatBody['alarm'].to_bytes(1, byteorder='little') + heartbeatBody[
        'voltage'].to_bytes(2, byteorder='little') + heartbeatBody['reserved'].to_bytes(1, byteorder='big')
    crc = crc16(tmpHeader + tmpBody)
    # crc = crc16.crc16xmodem(tmpHeader)
    return tmpHeader + tmpBody + crc.to_bytes(2, byteorder='big')


def procSensor(sensor):
    tmpHeader = b'\x20' + procSensorHeaderer(sensor)
    tmpBody = sensor['position_id'].to_bytes(1, byteorder='little') + sensor['state'].to_bytes(
        4, byteorder='little') + sensor['park_count'].to_bytes(2, byteorder='little') + sensor['voltage'].to_bytes(1, byteorder='little') + reserved_field.to_bytes(7, byteorder='little')
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
    # global sockLocal
    # sockLocal = doConnect(host, port)
    # send_data(procSensor())
    while True:
        logger.debug("begin send heartbeat")
        header['host_code_machine_id'] = 667
        thr = Greenlet(send_data, procHeartbeat())
        thr.run()
        time.sleep(3)
        header['host_code_machine_id'] = 666
        thr = Greenlet(send_data, procHeartbeat())
        thr.run()
        # send_data(procHeartbeat())
        time.sleep(300)


def loop_sensor_jingyi():
    # global sockLocal
    # sockLocal = doConnect(host, port)
    # send_data(procSensor())
    while True:
        time.sleep(1)
        ctime = time.time()
        try:
            for dev in dataPositionGlobal.keys():
                if dataPositionGlobal[dev]['need_send'] == True and ctime - dataPositionGlobal[dev]['last_receive_time'] > 18:
                    logger.debug("begin send sensor:%s,dev:%s",
                                 dev, dataPositionGlobal[dev]['last_sensor_info']['position_id'])
                    if dataPositionGlobal[dev]['last_send_state'] == 1 and dataPositionGlobal[dev]['last_sensor_info']['state'] == 1:
                        sensor = dataPositionGlobal[
                            dev]['last_sensor_info'].copy()
                        sensor['state'] = 0
                        thr = Greenlet(send_data, procSensor(sensor))
                        thr.run()
                        thr1 = Greenlet(send_data_delay, procSensor(dataPositionGlobal[
                            dev]['last_sensor_info']))
                        thr1.run()
                    else:
                        thr = Greenlet(send_data, procSensor(dataPositionGlobal[
                            dev]['last_sensor_info']))
                        thr.run()
                        # send_data(procSensor(dataPositionGlobal[
                        #     dev]['last_sensor_info']))
                    dataPositionGlobal[dev]['last_send_state'] = dataPositionGlobal[
                        dev]['last_sensor_info']['state']
                    dataPositionGlobal[dev]['need_send'] = False
        except Exception as error:
            error_msg = error
            logger.error(str(error_msg))


def send_data_delay(msg):
    time.sleep(15)
    send_data(msg)


def send_data(msg):
    sockLocal = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sockLocal.connect((host, port))
        logger.debug("begin send msg length: %s", len(msg))
        sockLocal.send(msg)
        logger.debug("send msg : %s", hexlify(msg).decode())
        recv = sockLocal.recv(1024)
        logger.debug("recv data :%s", recv)
        logger.debug("recv data :%s", hexlify(recv).decode())
        logger.debug("recv data len :%s", len(recv))
    except socket.error:
        logger.error("socket error,do reconnect ... waiting timeout")
        time.sleep(3)
        sockLocal.connect((host, port))
        sockLocal.send(msg)
        logger.debug("resend msg len: %s", len(msg))
        logger.debug("resend msg: %s", hexlify(msg).decode())
        recv = sockLocal.recv(1024)
        logger.debug("recv data :%s", recv)
        logger.debug("recv data :%s", hexlify(recv).decode())
    finally:
        sockLocal.close()


def proc_position_data(sensor):
    # dev = sensor['dev']
    if sensor['dev'] in dataPositionGlobal.keys():
        if dataPositionGlobal[sensor['dev']]['last_sensor_info']['state'] == 0 and sensor['state'] == 1:
            dataPositionGlobal[sensor['dev']]['park_count'] = dataPositionGlobal[
                sensor['dev']]['park_count'] + 1
            if dataPositionGlobal[sensor['dev']]['park_count'] > 255:
                dataPositionGlobal[sensor['dev']]['park_count'] = 0
        if dataPositionGlobal[sensor['dev']]['last_sensor_info']['state'] != sensor['state']:
            dataPositionGlobal[sensor['dev']]['need_send'] = True
        dataPositionGlobal[sensor['dev']]['last_receive_time'] = time.time()
        dataPositionGlobal[sensor['dev']]['last_sensor_info'] = sensor
    else:
        newPosition = {}
        newPosition['last_sensor_info'] = sensor
        newPosition['park_count'] = 0
        newPosition['last_receive_time'] = time.time()
        newPosition['need_send'] = True
        newPosition['last_send_state'] = 0
        dataPositionGlobal[sensor['dev']] = newPosition
    return dataPositionGlobal[sensor['dev']]['park_count']


def proc_message(item):
    try:
        logger.debug(str(item['data']))
        sensor = {}
        sensor['dev'] = str(item['data']).split(":")[1]
        sensor['position_id'] = get_position(sensor['dev'])
        logger.debug('get position with dev:%s', sensor['position_id'])
        if sensor['position_id'] > 0:
            sensor['position_id']
            if sensor['position_id'] >= 101:
                sensor['host_code_machine_id'] = 667
            else:
                sensor['host_code_machine_id'] = 666
            dataFromDev = db2.hgetall(item['data'])
            logger.debug(str(dataFromDev))
            dataFrame = dataFromDev[b'data']
            logger.debug('len:%s', len(dataFrame))
            firstByte = int(dataFrame[0])
            sensor['fcnt'] = dataFromDev[b'fcnt']
            frameType = (firstByte & 0b11110000) >> 4
            logger.debug('if weichuan frame type:%s', frameType)
            if (len(dataFrame) == 11 and frameType == 3) or (len(dataFrame) == 9 and frameType == 2) or (len(dataFrame) == 2 and frameType == 4):
                sensor['model'] = 'weichuan'
                logger.debug('weichuan sensor')
                sensor['state'] = (dataFrame[1] & 0b10000000) >> 7
                logger.debug('positionStatus:%s',
                             sensor['state'])
                voltage = (dataFrame[1] & 0b01111111)
                logger.debug('voltage:%s', voltage)
                sensor['voltage'] = voltage - 29
                sensor['park_count'] = proc_position_data(sensor)
                logger.debug('park_count:%s', dataPositionGlobal[
                    sensor['dev']]['park_count'])
                # send_data(procSensor(sensor))
                # send_data(procSensor())
                if len(dataFrame) > 2:
                    logger.debug('temperature:%d,%d' %
                                 (dataFrame[2], dataFrame[3]))
            elif firstByte == 171 and len(dataFrame) == 5:
                sensor['model'] = 'tuobao'
                logger.debug('tuobao sensor')
                sensor['state'] = (dataFrame[2] & 0b10000000) >> 7
                logger.debug('positionStatus:%s',
                             sensor['state'])
                voltage = (dataFrame[2] & 0b01111111)
                logger.debug('voltage:%s', voltage)
                logger.debug('status:%s', dataFrame[1] & 0b00001111)
                sensor['voltage'] = int(voltage * 7 / 100)
                sensor['park_count'] = proc_position_data(sensor)
                logger.debug('park_count:%s', dataPositionGlobal[
                    sensor['dev']]['park_count'])
                # send_data(procSensor(sensor))
    except Exception as error:
        error_msg = error
        logger.error(str(error_msg))


def get_position(dev_eui):
    if dev_eui == '2f03000010ffffff':
        return 128
    elif dev_eui == '9c02000010ffffff':
        return 127
    elif dev_eui == '0003000010ffffff':
        return 126
    elif dev_eui == 'bd03000010ffffff':
        return 125
    elif dev_eui == 'a903000010ffffff':
        return 124
    elif dev_eui == 'd002000010ffffff':
        return 123
    elif dev_eui == '5b02000010ffffff':
        return 122
    elif dev_eui == '7603000010ffffff':
        return 121
    elif dev_eui == '5803000010ffffff':
        return 120
    elif dev_eui == 'b203000010ffffff':
        return 119
    elif dev_eui == '6103000010ffffff':
        return 118
    elif dev_eui == '2e03000010ffffff':
        return 117
    elif dev_eui == '1003000010ffffff':
        return 116
    elif dev_eui == '2702000010ffffff':
        return 115
    elif dev_eui == '5b03000010ffffff':
        return 114
    elif dev_eui == 'ef01000010ffffff':
        return 113
    elif dev_eui == '0703000010ffffff':
        return 112
    elif dev_eui == '8602000010ffffff':
        return 111
    elif dev_eui == '1d03000010ffffff':
        return 110
    elif dev_eui == 'f302000010ffffff':
        return 109
    elif dev_eui == '2902000010ffffff':
        return 108
    elif dev_eui == '4803000010ffffff':
        return 107
    elif dev_eui == 'a402000010ffffff':
        return 106
    elif dev_eui == '1e02000010ffffff':
        return 105
    elif dev_eui == '0902000010ffffff':
        return 104
    elif dev_eui == 'ae02000010ffffff':
        return 103
    elif dev_eui == 'f002000010ffffff':
        return 102
    elif dev_eui == '8603000010ffffff':
        return 101
    elif dev_eui == '2f02000010ffffff':
        return 100
    elif dev_eui == 'dc02000010ffffff':
        return 99
    elif dev_eui == 'fb02000010ffffff':
        return 98
    elif dev_eui == '9999939a99999998':
        return 97
    elif dev_eui == '9999939a9999999b':
        return 96
    elif dev_eui == '9999939a9999999c':
        return 95
    elif dev_eui == 'e702000010ffffff':
        return 94
    elif dev_eui == '7202000010ffffff':
        return 93
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
    elif dev_eui == '5603000010ffffff':
        return 78
    elif dev_eui == '8502000010ffffff':
        return 76
    elif dev_eui == '1c03000010ffffff':
        return 74
    return 0


def listen_jingyi_request():
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
