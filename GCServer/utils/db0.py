import redis


class ConstDB:
    gateway = 'GATEWAY:'


class RedisDBConfig:
    HOST = '127.0.0.1'
    PORT = 6379
    DBID = 10
    PASSWORD = 'niotloraredis'

db0 = redis.StrictRedis(host=RedisDBConfig.HOST,
                        port=RedisDBConfig.PORT,
                        password=RedisDBConfig.PASSWORD,
                        db=RedisDBConfig.DBID)
