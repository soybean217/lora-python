import redis


class Tables8:
    http_push = 'HTTP_PUSH:'


db8 = redis.StrictRedis(host='127.0.0.1', port=6379, db=8, password='niotloraredis')