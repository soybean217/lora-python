import redis
from config import RedisHost, RedisPasswd, RedisPort

db6 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=6, password=RedisPasswd)

CHANNEL_TX_ACK = 'TX_ACK:'