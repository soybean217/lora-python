from database.db2 import db2, ConstDB2
from database.db4 import db4, ConstDB4
import random


def count(category):
    category += '_'
    keys = db2.keys(category + ConstDB4.GW + '*')
    for key in keys:
        id = key.decode().split(':')[1]
        last_len = db4.get(category + ConstDB4.LLEN + id)
        last_len = int(last_len) if last_len else 0
        now_len = db2.llen(category + ConstDB2.GW + id)
        time_list = db2.lrange(category + ConstDB2.GW + id, last_len, now_len - 1)
        list_len = len(time_list)
        size_list = []
        n = 5 if list_len > 5 else list_len
        for i in range(0, n):
            size_list.append(random.randint(0, list_len))
        for i in range(0, list_len):
            tt = int(time_list[i])
            tp = int(tt/600) * 600
            db4.hincrby(category + ConstDB4.GW + id + ':%s' % tp, 'n', 1)
            if i in size_list:
                keys = db2.keys(category + ConstDB2.T + '*:' + id + ':%s' % tt)
                size = int(db2.hget(keys[0], 'size'))
                db4.rpush(category + ConstDB4.SIZE + id + ':%s' % tt, size)
        db4.set(category + ConstDB4.LLEN + id, now_len)

if __name__ == '__main__':
    count('UP')
    count('DN')
