import random
from datetime import datetime, timezone
import pytz
from binascii import hexlify


def get_random_token():
    return random.getrandbits(16).to_bytes(length=2, byteorder='little')


def endian_reverse(addr):
    return int.to_bytes(int.from_bytes(addr, byteorder='big'), byteorder='little', length=4)


def iso_to_utc_ts(tstr):
    t = datetime.strptime(tstr, "%Y-%m-%dT%H:%M:%S.%fZ")
    t = t.replace(tzinfo=timezone.utc)
    return t.timestamp()


def bytes_to_hexstr(data):
    return hexlify(data).decode()


if __name__ == '__main__':
    from time import time
    tstr = '2016-12-27T02:04:10.867459Z'
    ts = iso_to_utc_ts(tstr)
    print(time(), ts)