import redis
from config import RedisHost, RedisPasswd, RedisPort

db4 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=4, password=RedisPasswd)


class ConstDB4:
    GW = 'GW:'
    LLEN = 'LLEN:'
    LTIME = 'LTIME:'
    SIZE = 'S:'


class Channel4:
    gis_gateway_location = 'gis_gateway_location:'
