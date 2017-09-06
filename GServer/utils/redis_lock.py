# def acquire_lock(conn, lockname, acquire_timeout=10):
#     # 128位随机标识符。
#     identifier = str(uuid.uuid4())
#
#     end = time.time() + acquire_timeout
#     while time.time() < end:
#         # 尝试取得锁。
#         if conn.setnx('lock:' + lockname, identifier):
#             return identifier
#
#         time.sleep(.001)
#
#     return False


from .db5 import db5, lock
from gevent import sleep
import uuid
import time
from redis.exceptions import WatchError
from binascii import hexlify, unhexlify


def acquire_lock(lockname, acquire_timeout=0.5, lock_timeout=0.2):
    end = time.time() + acquire_timeout
    identifier = str(uuid.uuid4())
    lockname = lock + lockname
    while time.time() < end:
        if db5.setnx(lockname, identifier):
            db5.expire(lockname, lock_timeout)
            return identifier
        sleep(0.01)
    return False


def release_lock(lockname, identifier):
    pipe = db5.pipeline()
    lockname = lock + lockname
    while True:
        try:
            pipe.watch(lockname)
            if pipe.get(lockname) == identifier:
                pipe.multi()
                pipe.delete(lockname)
                pipe.execute()
                return True
            pipe.unwatch()
            break
        except WatchError:
            pass
    return False


def start_device_block(dev_eui, data=None, lock_timeout=2):
    if isinstance(dev_eui, bytes):
        dev_eui = hexlify(dev_eui).decode()
    if data is None:
        data = time.time()
    if db5.set(dev_eui, data, nx=True, ex=lock_timeout):
        return True
    else:
        return False


def get_device_block_info(dev_eui):
    if isinstance(dev_eui, bytes):
        dev_eui = hexlify(dev_eui).decode()
    return db5.get(dev_eui)
