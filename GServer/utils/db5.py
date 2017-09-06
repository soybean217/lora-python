import redis
from config import RedisHost, RedisPasswd, RedisPort

db5 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=5, password=RedisPasswd)

lock = 'lock:'