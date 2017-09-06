from database.db2 import db2, ConstDB2
from binascii import hexlify


class Statistician:

    @staticmethod
    def count_uplink(dev_eui, start_ts=0, end_ts=-1):
        if end_ts == -1:
            end_ts = float('inf')
        info = []
        pipe = db2.pipeline()
        dev_eui = hexlify(dev_eui).decode()
        block_list = db2.lrange(ConstDB2.up_l_l + dev_eui, 0, -1)
        for block in block_list:
            msg_list = db2.lrange(ConstDB2.up_l + dev_eui + ':' + block.decode(), 0, -1)
            for msg in msg_list:
                pipe.hget(ConstDB2.up_m + dev_eui + ':' + msg.decode(), 'fcnt')
            fcnt_list = pipe.execute()
            retrans = {}
            loss = 0
            total = 0
            it = iter(fcnt_list)
            it_msg = iter(msg_list)
            first = 0
            check_first = True
            try:
                while True:
                    second = next(it)
                    second_msg = next(it_msg)
                    if second is not None:
                        second = int(second)
                    else:
                        db2.lrem(ConstDB2.up_l + dev_eui + ':' + block.decode(), count=1, value=second_msg)
                        continue
                    sub = second - first
                    if sub == 0:
                        retrans[second] = retrans[second] + 1 if retrans.get(second) else 1
                    elif sub > 1 and not check_first:
                        loss += sub - 1
                    else:
                        total += 1
                    check_first = False
                    first = second
            except StopIteration:
                pass
            fcnt_end = first
            if len(msg_list) > 0:
                retrans_count = {}
                for k, v in retrans.items():
                    retrans_count[v] = retrans_count[v] + 1 if retrans_count.get(v) else 1
                info.append({'retrans': retrans_count, 'loss': loss, 'total': total, 'fcnt':fcnt_end, 'start_ts': int(msg_list[0]), 'end_ts': int(msg_list[-1])})
        return info

    @staticmethod
    def count_retrans(dev_eui):
        info = []
        pipe = db2.pipeline()
        dev_eui = hexlify(dev_eui).decode()
        block_list = db2.lrange(ConstDB2.up_l_l + dev_eui, 0, -1)
        for block in block_list:
            msg_list = db2.lrange(ConstDB2.up_l + dev_eui + ':' + block.decode(), 0, -1)
            for msg in msg_list:
                pipe.hget(ConstDB2.up_m + dev_eui + ':' + msg.decode(), 'fcnt')
            fcnt_list = pipe.execute()
            retrans = {}
            it = map(lambda x, y: (int(x), int(y)), msg_list, fcnt_list)
            try:
                ts0, fcnt0 = next(it)
                while True:
                    ts1, fcnt1 = next(it)
                    sub = fcnt1 - fcnt0
                    if sub == 0:
                        g_id = db2.zrevrange(ConstDB2.up_gw_s + dev_eui + ':%s' % str(ts0), 0, 0)
                        print(ConstDB2.up_gw_s + dev_eui + ':%s' % str(ts0), g_id)
                        freq = float(db2.hget(ConstDB2.up_t + dev_eui + ':' + g_id[0].decode() + ':%s' % ts0, 'freq'))
                        count = retrans.get(freq)
                        retrans[freq] = count + 1 if count else 1
                    ts0, fcnt0 = ts1, fcnt1
            except StopIteration:
                pass
            if len(msg_list) > 0:
                info.append({'retrans': retrans, 'start_ts': int(msg_list[0]), 'end_ts': int(msg_list[-1])})
        return info