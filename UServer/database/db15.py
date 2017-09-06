import redis
from config import RedisHost, RedisPasswd, RedisPort

db15 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=15, password=RedisPasswd)


class ConstDB15:
    M = 'M:'
    G = 'G:'


