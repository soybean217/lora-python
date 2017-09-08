from uuid import getnode

mac = getnode()
MAC = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
MACSERVER = 'E4:1F:13:1C:67:54'  # Server mac address of bond0

if MAC == MACSERVER:
    # server side
    HOST = '183.230.40.231'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://pro_nwkserver:niotlorasql@localhost:3312/nwkserver'
    RedisPort = 6380
else:
    # local side
    HOST = '127.0.0.1'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://nwkserver:niotlorasql@localhost:3306/nwkserver'
    RedisPort = 6379

RedisHost = '127.0.0.1'
RedisPasswd = 'niotloraredis'
