import redis


class ConstDB9:
    released_addr = 'RELEASED_ADDR'
    current_block = 'CUR_BLOCK'
    current_num = 'CUR_NUM'
    block = 'BLOCK:'


db9 = redis.StrictRedis(host='127.0.0.1', port=6379, db=9, password='niotloraredis')