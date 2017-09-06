from datetime import datetime, timedelta
import time
from database.db0 import db0, ConstDB
from binascii import hexlify
from database.db3 import db3, ConstDB3
from database.db4 import db4, ConstDB4


class Statistician:
    def __init__(self, id):
        self.key = ConstDB.statistics_freq + hexlify(id).decode() + ':'
        self.id = id

    @staticmethod
    def count_link(id, category, start_ts=0, end_ts=-1):
        if end_ts == -1:
            end_ts = float('inf')
        category = category + '_'
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

    # @staticmethod
    # def count_link(id, category='UP', start_ts=0, end_ts=-1):
    #     hex_id = hexlify(id).decode()
    #     key = category + '_GW:' + hex_id
    #     llen = db2.llen(key)
    #     i = 0
    #     start = 0
    #     end = llen
    #     desc = True
    #     asce = True
    #     scheck = True if start_ts > 0 else False
    #     echeck = True if end_ts > 0 else False
    #     while i < llen/2:
    #         if not (scheck or echeck) or not (desc or asce):
    #             break
    #         if asce:
    #             s_ts = int(db2.lindex(key, i))
    #         if desc:
    #             e_ts = int(db2.lindex(key, llen - i - 1))
    #         if scheck and s_ts < start_ts:
    #             if e_ts < start_ts:
    #                 asce = False
    #                 start = llen - i - 1
    #             else:
    #                 start = i
    #         else:
    #             scheck = False
    #         if echeck and e_ts > end_ts:
    #             if s_ts > end_ts:
    #                 desc = False
    #                 end = i
    #             else:
    #                 end = llen-i-1
    #         else:
    #             echeck = False
    #         i += 1
    #     count = end - start - 1
    #
    #     if count <= 0:
    #         count = 0
    #     else:
    #         size_list = []
    #         s_l = []
    #         n = 3 if count > 3 else count
    #         for i in range(0, n):
    #             size_list.append(random.randint(start, end))
    #         for index in size_list:
    #             ts = db2.lindex(key, index)
    #             keys = db2.keys(category + '_TSET:*' + ':' + hex_id + ':' + ts.decode())
    #             s_l.append(int(db2.hget(keys[0], 'size')))
    #         avr_size = sum(s_l)/len(s_l)
    #         count = int(avr_size*count)
    #     return count
        # keys = db2.keys(ConstDB2.up_tset + '*:' + hexlify(id).decode() + ':*')
        # count = 0
        # for key in keys:
        #     ts = int(key.decode().split(':')[3])
        #     if start_ts < ts and ((end_ts < 0) or (ts < end_ts)):
        #         try:
        #             size = int(db2.hget(key, 'size'))
        #             count += size
        #         except Exception as error:
        #             print(error)
        # return count

        # keys = db2.keys(ConstDB2.dn_tset + '*:' + hexlify(id).decode() + ':*')
        # count = 0
        # for key in keys:
        #     ts = int(key.decode().split(':')[4])
        #     if start_ts < ts and ((end_ts < 0) or (ts < end_ts)):
        #         try:
        #             size = int(db2.hget(key, 'size'))
        #             count += size
        #         except Exception as error:
        #             print(error)
        # return count

    @staticmethod
    def count_online(id):
        hex_id = hexlify(id).decode()
        t_list = db3.lrange(ConstDB3.P_GATEWAY + hex_id, 0, -1)
        latest_time = db3.get(ConstDB3.T_GATEWAY + hex_id)
        p_list = []
        for i in range(1, len(t_list), 2):
            p_list.append([int(data) for data in t_list[i:i+2]])
        if len(p_list) > 0:
            p_list[-1].append(int(latest_time))
        elif latest_time:
            p_list.append([0, int(latest_time)])
        return p_list

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
                        res[freq] = [0] * 30
                    res[freq][x] += int(value)
        new_res = []
        for freq, num_list in res.items():
            new_res.append({'name': freq,
                            'data': num_list})
        return new_res

    def count_in_hourly(self):
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
                        res[freq] = [0] * 24
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