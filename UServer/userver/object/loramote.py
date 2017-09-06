from binascii import hexlify
from database.db15 import db15, ConstDB15
from database.db2 import db2, ConstDB2
from utils.log import Logger
import threading


class LoRaMote:
    def __init__(self, dev_eui):
        self.dev_eui = hexlify(dev_eui).decode()

    # def uplinks(self, g_id=None, start_ts=0, end_ts=-1):
    #     m_list = []
    #     if end_ts == -1:
    #         end_ts = float('inf')
    #     cursor = 0
    #     while True:
    #         result = db15.scan(cursor=cursor, match=ConstDB15.M + self.dev_eui + ':*')
    #         cursor = result[0]
    #         m_key_list = result[1]
    #         thread = threading.Thread(target=self.ttt, args=(g_id, start_ts, end_ts, m_key_list, m_list))
    #         thread.start()
    #         thread.join()
    #         # print(cursor, m_list)
    #         if cursor == 0:
    #             break
    #     return m_list

    def uplinks(self, g_id=None, start_ts=0, end_ts=-1):
        m_list = []
        if end_ts == -1:
            end_ts = float('inf')
        block_list = db2.lrange(ConstDB2.up_l_l + self.dev_eui, 0, -1)
        for block in block_list:
            block = int(block)
            if block >= end_ts:
                continue
            block_end = int(db2.lindex(ConstDB2.up_l + self.dev_eui + ':%s' % block, -1))
            if block_end < start_ts:
                continue
            m_ts_list = db2.lrange(ConstDB2.up_l + self.dev_eui + ':%s' % block, 0, -1)
            it = iter(m_ts_list)
            m_ts_list = []
            for m_ts in it:
                m_ts = int(m_ts)
                if start_ts <= m_ts <= end_ts:
                    m_ts_list.append(m_ts)
                    m_info = db15.hgetall(ConstDB15.M + self.dev_eui + ':%s' % m_ts)
                    if len(m_info) < 1:
                        print(ConstDB15.M + self.dev_eui + ':%s' % m_ts, 'no m_info')
                        continue
                    m_info = self.format_msg(m_info)
                    m_info['ts'] = m_ts
                    if g_id:
                        g_info = db15.hgetall(ConstDB15.G + self.dev_eui + ':' + g_id + ':' + str(m_ts))
                        g_info = self.format_msg(g_info)
                        m_info.update(g_info)
                    else:
                        g_id_list = db2.zrevrange('%s%s:%s' % (ConstDB2.up_gw_s, self.dev_eui, m_ts), 0, -1)
                        pipe = db15.pipeline()
                        for g_key in g_id_list:
                            pipe.hgetall(ConstDB15.G + self.dev_eui + ':' + g_key.decode() + ':' + str(m_ts))
                        hh = pipe.execute()
                        g_info = list(map(lambda x, y: dict(self.format_msg(x), gw=y.decode()), hh, g_id_list))
                        best = g_info[0]
                        m_info.update(best)
                        m_info.update({'more_gateways': g_info[1: -1]})
                    m_list.append(m_info)
        return m_list

    def ttt(self, g_id, start_ts, end_ts, m_key_list, m_list):
        for m_key in m_key_list:
            ts = int(m_key.decode().split(':')[2])
            if start_ts < ts < end_ts:
                m_info = db15.hgetall(m_key)
                m_info = self.format_msg(m_info)
                m_info['ts'] = ts
                if g_id:
                    g_info = db15.hgetall(ConstDB15.G + self.dev_eui + ':' + g_id + ':' + str(ts))
                    g_info = self.format_msg(g_info)
                    m_info.update(g_info)
                else:
                    g_id_list = db2.zrevrange('%s%s:%s' % (ConstDB2.up_gw_s, self.dev_eui, ts), 0, -1)
                    pipe = db15.pipeline()
                    for g_key in g_id_list:
                        pipe.hgetall(ConstDB15.G + self.dev_eui + ':' + g_key.decode() + ':' + str(ts))
                    hh = pipe.execute()
                    g_info = list(map(lambda x, y: dict(self.format_msg(x), gw=y.decode()), hh, g_id_list))
                    best = g_info[0]
                    m_info.update(best)
                    m_info.update({'more_gateways': g_info[1: -1]})
                m_list.append(m_info)

    @classmethod
    def format_msg(cls, dd):
        new_dd = {}
        for k, v in dd.items():
            k = k.decode()
            new_dd[k] = cls.format_data(k, v)
        return new_dd

    @staticmethod
    def format_data(name, value):
        if name in ('rssi', 'fcnt', 'alt', 'dist'):
            value = int(float(value))
        elif name in ('lat', 'lng', 'lsnr', 'freq'):
            value = float(value)
        else:
            value = value.decode()
        return value

    def stat_rssi_snr(self, g_id=None, start_ts=0, end_ts=-1):
        info = []
        if end_ts == -1:
            end_ts = float('inf')
        if g_id is not None:
            g_id = hexlify(g_id).decode()
        cursor = 0
        while True:
            result = db15.scan(cursor=cursor, match=ConstDB15.M + self.dev_eui + ':*')
            cursor = result[0]
            m_key_list = result[1]
            for m_key in m_key_list:
                try:
                    ts = int(m_key.decode().split(':')[2])
                    if start_ts < ts < end_ts:
                        lng, lat, alt = db15.hmget(m_key, ['lng', 'lat', 'alt'])
                        if g_id:
                            one = db15.hmget(ConstDB15.G + self.dev_eui + ':' + g_id + ':' + str(ts), ['rssi', 'lsnr'])
                            rssi = float(one[0])
                            lsnr = float(one[1])
                        else:
                            g_key_list = db2.zrevrange('%s%s:%s' % (ConstDB2.up_gw_s, self.dev_eui, ts), 0, 0)
                            # pipe = db15.pipeline()
                            # for g_key in g_key_list:
                            #     pipe.hmget(g_key, ['rssi', 'lsnr'])
                            # hh = pipe.execute()
                            # best = max(hh, key=lambda x: float(x[0]))
                            # lsnr = float(best[1])
                            # rssi = float(best[0])
                            g_key = g_key_list[0].decode()
                            best = db15.hmget('%s%s:%s:%s' % (ConstDB15.G, self.dev_eui, g_key, ts), ['rssi', 'lsnr'])
                            rssi, lsnr = float(best[0]), float(best[1])
                        info.append({'lng': float(lng), 'lat': float(lat), 'alt': float(alt), 'rssi': rssi, 'lsnr': lsnr})
                except Exception as error:
                    Logger.error('LoRaMote: %s' % error)
            if cursor == 0:
                break
        return info

    def stat_retrans(self, start_ts=0, end_ts=-1):
        dev_eui = self.dev_eui
        if end_ts == -1:
            end_ts = float('inf')
        info = {}
        pipe = db15.pipeline()
        block_list = db2.lrange(ConstDB2.up_l_l + dev_eui, 0, -1)
        for block in block_list:
            block = int(block)
            if block >= end_ts:
                continue
            block_end = int(db2.lindex(ConstDB2.up_l + dev_eui + ':%s' % block, -1))
            if block_end < start_ts:
                continue
            m_ts_list = db2.lrange(ConstDB2.up_l + dev_eui + ':%s' % block, 0, -1)
            it = iter(m_ts_list)
            m_ts_list = []
            for m_ts in it:
                m_ts = int(m_ts)
                if start_ts <= m_ts <= end_ts:
                    m_ts_list.append(m_ts)
                    pipe.hmget(ConstDB15.M + dev_eui + ':%s' % m_ts, ['fcnt', 'lng', 'lat', 'alt'])
            fcnt_list = pipe.execute()
            try:
                it = map(lambda x, y: (int(x), int(y[0]), float(y[1]), float(y[2]), float(y[3])), m_ts_list, fcnt_list)
                ts0, fcnt0, lng0, lat0, alt0 = next(it)
                while True:
                    ts1, fcnt1, lng1, lat1, alt1 = next(it)
                    sub = fcnt1 - fcnt0
                    if sub == 0:
                        location = (lng1, lat1, alt1)
                        count = info.get(location)
                        info[location] = count + 1 if count else 1
                    ts0, fcnt0 = ts1, fcnt1

            except (TypeError, StopIteration):
                pass
        info = [{'lng': x[0], 'lat':x[1], 'alt':x[2], 'retrans':y} for x, y in info.items()]
        return info

    def stat_retrans_dist(self, g_id=None, start_ts=0, end_ts=-1):
        if g_id:
            g_id = hexlify(g_id).decode()
        dev_eui = self.dev_eui
        if end_ts == -1:
            end_ts = float('inf')
        info = [[0, 0] for i in range(8)]
        pipe = db15.pipeline()
        block_list = db2.lrange(ConstDB2.up_l_l + dev_eui, 0, -1)
        for block in block_list:
            block = int(block)
            if block >= end_ts:
                continue
            block_end = int(db2.lindex(ConstDB2.up_l + dev_eui + ':%s' % block, -1))
            if block_end < start_ts:
                continue
            m_ts_list = db2.lrange(ConstDB2.up_l + dev_eui + ':%s' % block, 0, -1)
            it = iter(m_ts_list)
            m_ts_list = []
            for m_ts in it:
                m_ts = int(m_ts)
                if start_ts <= m_ts <= end_ts:
                    m_ts_list.append(m_ts)
                    pipe.hmget(ConstDB15.M + dev_eui + ':%s' % m_ts, ['fcnt', 'lng', 'lat', 'alt'])
            fcnt_list = pipe.execute()
            try:
                it = map(lambda x, y: (int(x), int(y[0]), float(y[1]), float(y[2]), float(y[3])), m_ts_list, fcnt_list)
                ts0, fcnt0, lng0, lat0, alt0 = next(it)
                while True:
                    retrans = 0
                    ts1, fcnt1, lng1, lat1, alt1 = next(it)
                    sub = fcnt1 - fcnt0
                    if g_id:
                        dist = float(db15.hget(ConstDB15.G + dev_eui + ':' + g_id + ':%s' % ts0, 'dist'))
                    else:
                        g_key_list = db2.zrevrange('%s%s:%s' % (ConstDB2.up_gw_s, self.dev_eui, ts0), 0, 0)
                        g_key = g_key_list[0].decode()
                        dist = float(db15.hget(ConstDB15.G + dev_eui + ':' + g_key + ':%s' % ts0, 'dist'))
                    level = self.get_distance_level(dist)
                    if sub == 0:
                        info[level][1] += 1
                    else:
                        info[level][0] += 1
                    ts0, fcnt0 = ts1, fcnt1
            except (TypeError, StopIteration):
                pass
        info = list(map(lambda x, y: {'dist': x, 'total': y[0], 'retrans': y[1]}, self.distance_level, info))
        return info

    distance_level = [['0-50'], ['50-150'], ['150-400'], ['400-1000'], ['1000-3000'], ['3000-8000'], ['8000-20000'], ['>20000']]

    @staticmethod
    def get_distance_level(dist):
        if 0 <= dist < 50:
            return 0
        if 50 <= dist < 150:
            return 1
        if 150 <= dist < 400:
            return 2
        if 400 <= dist < 1000:
            return 3
        if 1000 <= dist < 3000:
            return 4
        if 3000 <= dist < 8000:
            return 5
        if 8000 <= dist < 20000:
            return 6
        else:
            return 7


if __name__ == '__main__':
    print(len(db15.hgetall('hello')))