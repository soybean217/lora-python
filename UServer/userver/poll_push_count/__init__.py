from datetime import datetime, timedelta
import time
from collections import OrderedDict
from userver.database.db0 import db0,ConstDB
from utils.log import logger


class ConstStatis:
    dev = 'DEV'
    group = 'GROUP'


class Statistician(object):
    def __init__(self, eui, type):
        if type == 'DEV':
            self.eui = ConstDB.dev + eui
        elif type == 'GROUP':
            self.eui = ConstDB.group + eui
        self.push_name = ConstDB.statistics_up + eui + ':' + datetime.now().strftime("%Y-%m-%d")
        self.poll_name = ConstDB.statistics_down + eui + ':' + datetime.now().strftime("%Y-%m-%d")

    def push_sum_of_one_day(self):
        """
        返回上行整一天的和
        :return:
        """
        res = db0.hgetall(self.push_name)
        values = res.values()
        sum = 0
        for v in values:
            sum += int(v)
        return sum

    def poll_sum_of_one_day(self):
        """
        返回下行整一天的和
        :return:
        """
        res = db0.hgetall(self.poll_name)
        values = res.values()
        sum = 0
        for v in values:
            sum += int(v)
        return sum

    def push_count_in_daily(self):
        """
        一天为单位计数
        :return:返回30天前的上行数据
        """
        res = OrderedDict()
        for x in range(0, 30):
            date = datetime.now() - timedelta(x)
            timestamp = int(date.timestamp())
            date_str = date.strftime("%Y-%m-%d")
            name = self.push_name.rsplit(':', 1)[0] + ':' + date_str
            sum = 0
            values = db0.hgetall(name).values()
            for v in values:
                sum += int(v)
            res[timestamp] = sum
        return res

    def poll_count_in_daily(self):
        """
        一天为单位计数
        :return:返回30天前的下行数据
        """
        res = OrderedDict()
        for x in range(0, 30):
            date = datetime.now() - timedelta(x)
            timestamp = int(date.timestamp())
            date_str = date.strftime("%Y-%m-%d")
            name = self.poll_name.rsplit(':', 1)[0] + ':' + date_str
            sum = 0
            values = db0.hgetall(name).values()
            for v in values:
                sum += int(v)
            res[timestamp] = sum
        return res

    def push_count_in_hour(self):
        """
        二十四小时前计数,
        :return: 每小时对应的数量
        """
        current_hour = datetime.now().hour
        today = self.push_name.rsplit(':', 1)[1]

        # 昨天距离现在24小时内每小时的数据
        yestoday_count = OrderedDict()
        if current_hour != 23:
            yestoday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            yestoday_name = self.push_name.rsplit(':', 1)[0] + ':' + yestoday
            yestoday_hour = current_hour + 1

            for hour in range(yestoday_hour, 24):
                key = str(hour)
                count_key = yestoday + ' ' + str(hour)
                count = db0.hget(yestoday_name, key)
                if count:
                    count = int(count.decode())
                else:
                    count = 0
                timestamp = int(datetime.strptime(count_key, '%Y-%m-%d %H').timestamp())
                yestoday_count[timestamp] = count

        # 今天的每个小时的数据
        today_count = OrderedDict()
        for hour in range(0, current_hour + 1):
            key = str(hour)
            count_key = today + ' ' + str(hour)
            count = db0.hget(self.push_name, key)
            if count:
                count = int(count.decode())
            else:
                count = 0
            timestamp = int(datetime.strptime(count_key, '%Y-%m-%d %H').timestamp())
            today_count[timestamp] = count

        today_count.update(yestoday_count)

        return today_count

    def poll_count_in_hour(self):
        """
        二十四小时前计数,
        :return: 每小时对应的数量
        """
        current_hour = datetime.now().hour
        today = self.poll_name.rsplit(':', 1)[1]

        yestoday_count = OrderedDict()
        if current_hour != 23:
            yestoday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            yestoday_name = self.poll_name.rsplit(':', 1)[0] + ':' + yestoday
            yestoday_hour = current_hour + 1

            for hour in range(yestoday_hour, 24):
                key = str(hour)
                count_key = yestoday + ' ' + str(hour)
                count = db0.hget(yestoday_name, key)
                if count:
                    count = int(count.decode())
                else:
                    count = 0
                count_key = int(datetime.strptime(count_key, '%Y-%m-%d %H').timestamp())
                yestoday_count[count_key] = count

        today_count = OrderedDict()
        for hour in range(0, current_hour + 1):
            key = str(hour)
            count_key = today + ' ' + str(hour)
            count = db0.hget(self.poll_name, key)
            if count:
                count = int(count.decode())
            else:
                count = 0
            count_key = int(datetime.strptime(count_key, '%Y-%m-%d %H').timestamp())
            today_count[count_key] = count

        today_count.update(yestoday_count)

        return today_count


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



if __name__ == '__main__':
    statistician = Statistician('be7a0000000ffffe')
    data = statistician.push_count_in_hour()
    print(statistician.poll_count_in_hour())
    print(statistician.push_sum_of_one_day())
    print(statistician.poll_sum_of_one_day())
    print(statistician.push_count_in_daily())
    print(statistician.poll_count_in_daily())