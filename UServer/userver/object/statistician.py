from datetime import datetime, timedelta
from database.db0 import db0, ConstDB


class ConstStatis:
    dev = 'DEV'
    group = 'GROUP'


class Statistician:
    def __init__(self, eui, type):
        if type == 'DEV':
            self.eui = ConstDB.dev + eui
        elif type == 'GROUP':
            self.eui = ConstDB.group + eui
        self.key_up = ConstDB.statistics_up + eui + ':'
        self.key_down = ConstDB.statistics_down + self.eui + ':'
        self.key_retrans = ConstDB.statistics_retrans + eui + ':'

    def msg_up_count_in_daily(self):
        """
        一天为单位计数
        :return:返回30天前的上行数据
        """
        return self.count_in_daily(self.key_up)

    def msg_down_count_in_daily(self):
        """
        一天为单位计数
        :return:返回30天前的下行数据
        """
        return self.count_in_daily(self.key_down)

    def msg_retrans_count_in_daily(self):
        """
        一天为单位计数
        :return:返回30天前的重传数据
        """
        return self.count_in_daily(self.key_retrans)

    def msg_up_count_in_hour(self):
        """
        二十四小时前计数,
        :return: 每小时对应的数量
        """
        return self.count_in_hour(self.key_up)

    def msg_retrans_count_in_hour(self):
        """
        一天为单位计数
        :return:返回30天前的重传数据
        """
        return self.count_in_hour(self.key_retrans)

    def msg_down_count_in_hour(self):
        """
        二十四小时前计数,
        :return: 每小时对应的数量
        """
        return self.count_in_hour(self.key_down)

    @staticmethod
    def count_in_daily(key):
        res = []
        cur_time = datetime.now()
        for x in range(0, 30):
            date = cur_time - timedelta(29-x)
            name = key + date.strftime("%Y-%m-%d")
            sum = 0
            values = db0.hgetall(name).values()
            for v in values:
                sum += int(v)
            res.append(sum)
        return res

    @staticmethod
    def count_in_hour(key):
        res = []
        cur_time = datetime.now()
        cur_hour = cur_time.hour
        today_key = key + cur_time.strftime('%Y-%m-%d')
        yesterday_key = key + (cur_time - timedelta(days=1)).strftime('%Y-%m-%d')
        for x in range(0, 24):
            hour = cur_hour - 23 + x
            if hour < 0:
                data = db0.hget(yesterday_key, hour+24)
            else:
                data = db0.hget(today_key, hour)
            if not data:
                data = 0
            else:
                data = int(data)
            res.append(data)
        return res

