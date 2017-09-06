import redis


class Tables1:
    dev = 'DEV:'
    addr = 'ADDR:'
    dev_nonce = 'DEV_NONCE:'


class Channel1:
    join_req_alarm = 'join_request:'
    join_accept_alarm = 'join_accept:'
    join_success_alarm = 'join_success:'


db1 = redis.StrictRedis(host='127.0.0.1', port=6379, db=11, password='niotloraredis')