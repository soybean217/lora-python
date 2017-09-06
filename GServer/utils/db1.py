import redis
from config import RedisHost, RedisPasswd, RedisPort

db1 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=11, password=RedisPasswd)


class Channel1:
    join_req_alarm = 'join_request:'
    join_accept_alarm = 'join_accept:'
    join_success_alarm = 'join_success:'


# class RedisDBConfig:
#     HOST = '127.0.0.1'
#     PORT = 6379
#     DBID = 0
#     PASSWORD = 'niotloraredis'
#
#
# class RedisDB(object):
#     def __init__(self):
#         if not hasattr(RedisDB, 'pool'):
#             RedisDB.create_pool()
#         self._connection = redis.StrictRedis(connection_pool=RedisDB.pool)


# def set_addr_pool(db):
#     numbers = set(range(0x2000))
#     for i in range(0x1000):
#         db.sadd('DEV_ADDR_POOL:'+str(i), *numbers)
#
#
# def pop_addr(db):
#     return db.spop('DEV_ADDR_POOL:')

# if __name__ == '__main__':
    # set_addr_pool()
#     setup = '''
# from db1 import set_addr_pool,pop_addr
# import redis
# db2 = redis.StrictRedis(host='127.0.0.1', port=6379, db=2, password='niotloraredis')
#     '''
#     # a = timeit.timeit('set_addr_pool(db2)', number=1, setup=setup)
#     a = timeit.timeit('pop_addr(db2)', number=1, setup=setup)
#     # b = timeit.timeit('set(range(0x10000))', number=1)
#     print('finish')
#     print(a)

    # t = timeit.Timer('set_addr_pool')
    # t.timeit()