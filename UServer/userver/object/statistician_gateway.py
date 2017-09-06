from datetime import datetime, timedelta
import time
from database.db0 import db0,ConstDB
from binascii import hexlify
from database.db3 import db3, ConstDB3
from database.db4 import db4, ConstDB4


class ConstStatis:
    dev = 'DEV'
    group = 'GROUP'


class Statistician(object):
    def __init__(self, id):
        self.key = ConstDB.statistics_freq + hexlify(id).decode() + ':'

    @staticmethod
    def count_link(id, category, start_ts=0, end_ts=-1):
        if end_ts == -1:
            end_ts = float('inf')
        category += '_'
        id = hexlify(id).decode()
        keys = db4.keys(category + ConstDB4.GW + id + ':*')
        count = 0
        for key in keys:
            key_split = key.decode().split(':')
            ts = int(key_split[2])
            if start_ts - ts > 600:
                continue
            elif ts - end_ts > 600:
                continue
            n, s = db4.hmget(key, ['n', 's'])
            n = int(n)
            if s:
                s = int(s)
            else:
                s_list = db4.lrange(category + ConstDB4.SIZE + id + ':%s' % ts, 0, -1)
                if len(s_list) == 0:
                    random_s_list = db4.keys(category + ConstDB4.SIZE + id + ':*')
                    s_list = db4.lrange(random_s_list[0], 0, -1)
                s_list = [int(size) for size in s_list]
                s = round(sum(s_list)/len(s_list))
                db4.hset(key, 's', s)
            sub_ts = 0
            if start_ts > ts:
                sub_ts += start_ts - ts
            if end_ts - 600 < ts:
                sub_ts += ts + 600 - end_ts
            n = int((600 - sub_ts) / 600 * n)
            count += n * s
        return count

    def count_in_daily(self):
        """
        一天为单位计数
        :return:返回30天前的上行数据
        """
        res = {}
        cur_time = datetime.now()
        for x in range(0, 30):
            date = cur_time - timedelta(29-x)
            date_str = date.strftime("%Y-%m-%d")
            keys = db0.keys(self.key + date_str + ':*')
            for key in keys:
                data = db0.hgetall(key)
                for freq, value in data.items():
                    freq = float(freq)
                    if freq not in res.keys():
                        res[freq] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    res[freq][x] += int(value)
        new_res = []
        for freq, num_list in res.items():
            new_res.append({'name': freq,
                            'data': num_list})
        return new_res

    def count_in_hour(self):
        """
        二十四小时前计数,
        :return: 每小时对应的数量
        """
        res = {}
        cur_time = datetime.now()
        cur_hour = cur_time.hour
        today_key = self.key + cur_time.strftime('%Y-%m-%d')
        yesterday_key = self.key + (cur_time - timedelta(days=1)).strftime('%Y-%m-%d')
        for x in range(0, 24):
            hour = cur_hour - 23 + x
            if hour < 0:
                data = db0.hgetall(yesterday_key + ':' + str(hour+24))
            else:
                data = db0.hgetall(today_key + ':' + str(hour))
            if data:
                for freq, value in data.items():
                    freq = float(freq)
                    if freq not in res.keys():
                        res[freq] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                    res[freq][x] = int(value)
        new_res = []
        for freq, num_list in res.items():
            new_res.append({'name': freq,
                            'data': num_list})
        return new_res


def current_timestamp():
    """
    当前时间戳，精确到秒
    :return: int 时间戳
    """
    return int(time.time())


def get_current_hour():
    """
    当前小时数
    :return: int
    """
    return datetime.now().hour
