from utils.db0 import db0, ConstDB0
from binascii import hexlify


class Resend:
    def __init__(self, dev_eui):
        self.dev_eui = dev_eui

    def set_resend_data(self, data, maxcnt=5):
        dict = {'data': data, 'maxcnt': maxcnt}
        db0.hmset(ConstDB0.resend + hexlify(self.dev_eui).decode(), dict)
        # db0.setex(ConstDB0.resend + hexlify(self.dev_eui).decode(), 100, data)

    def get_resend_data(self):
        return db0.hgetall(ConstDB0.resend + hexlify(self.dev_eui).decode())

    def update_repeat_cnt(self):
        return db0.hincrby(ConstDB0.resend + hexlify(self.dev_eui).decode(), 'maxcnt', amount=-1)

    def check_exist(self):
        return db0.exists(ConstDB0.resend + hexlify(self.dev_eui).decode())

    def del_retrans_down(self):
        return db0.delete(ConstDB0.resend + hexlify(self.dev_eui).decode())