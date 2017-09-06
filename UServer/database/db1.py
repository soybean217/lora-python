import redis
from config import RedisHost, RedisPasswd, RedisPort


class Tables1:
    dev = 'DEV:'
    addr = 'ADDR:'
    dev_nonce = 'DEV_NONCE:'


class Channel1:
    join_req_alarm = 'join_request:'
    join_accept_alarm = 'join_accept:'
    join_success_alarm = 'join_success:'
    join_error_alarm = 'join_error:'


db1 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=11, password=RedisPasswd)