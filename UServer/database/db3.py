import redis
from config import RedisHost, RedisPasswd, RedisPort

db3 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=3, password=RedisPasswd)


class ConstDB3:
    P_GATEWAY = 'P_GATEWAY:'
    T_GATEWAY = 'T_GATEWAY:'