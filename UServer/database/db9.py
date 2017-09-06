import redis
from config import RedisHost, RedisPasswd, RedisPort


class ConstDB9:
    released_addr = 'RELEASED_ADDR'
    current_block = 'CUR_BLOCK'
    current_num = 'CUR_NUM'
    block = 'BLOCK:'


db9 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=9, password=RedisPasswd)