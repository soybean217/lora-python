from database.db2 import db2
import time


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
    ps.subscribe("up_alarm:9999939a00000000")
    # ps.subscribe("up_alarm:1020304050607080")
    while True:
        for item in ps.listen():
            print(str(item))
            if item['type'] == 'message':
                print(str(item['data']))
                dataFromDev = db2.hgetall(item['data'])
                print(str(dataFromDev))
                dataFrame = dataFromDev[b'data']
                print(str(dataFrame))
                print(len(dataFrame))
                firstByte = int(dataFrame[0])
                print("firstByte:", firstByte)
                frameType = (firstByte & 0b11110000) >> 4
                print('frame type:', frameType)
                if (len(dataFrame) == 11 and frameType == 3) or (len(dataFrame) == 9 and frameType == 2) or (len(dataFrame) == 2 and frameType == 4):
                    positionStatus = (dataFrame[1] & 0b10000000) >> 7
                    print('positionStatus:', positionStatus)
                    voltage = (dataFrame[1] & 0b01111111)
                    print('voltage:', voltage)
                    if len(dataFrame) > 2:
                        print(dataFrame[2:4])
                        # print(str(item['data'].decode()))
                        # print(str(db2.get(item['data'].decode())))
                        # thr = Greenlet(process_join_request, data)
                        # thr.run()
