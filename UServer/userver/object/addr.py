from database.db9 import db9, ConstDB9
from binascii import hexlify
from database.db0 import db0, ConstDB
from database.db1 import db1
from utils.errors import KeyDuplicateError
from utils.log import logger

"""
Bit#     |31..25|24..00
---------|------|-------
addr bits|NwkID |NwkAddr

Total addr: 2^25 = 33554432
block size 2^5 = 32
block num 2^20 = 1048576

cur_block: current block num
cur_num: current num in current block



"""

NwkID = 22


class AddrManger:

    @staticmethod
    def addr_available(addr):
        addr_key = ConstDB.addr + hexlify(addr).decode()
        if db0.exists(addr_key) or db1.exists(addr_key):
            logger.debug('ADDR KeyDuplicateError db0 %s' % db0.get(addr_key))
            logger.debug('ADDR KeyDuplicateError db1 %s' % db1.get(addr_key))
            raise KeyDuplicateError(addr_key)

    @staticmethod
    def endian_reverse(addr):
        return int.to_bytes(int.from_bytes(addr, byteorder='big'), byteorder='little', length=4)

    @staticmethod
    def recycle_addr(dev_addr):
        """
        :param dev_addr: bytes
        :return:
        """
        dev_addr = int.from_bytes(dev_addr, byteorder='big')
        nwk_id = dev_addr >> 25
        if NwkID == nwk_id:
            nwk_addr = dev_addr & 0x1FFFFFF
            db9.lpush(ConstDB9.released_addr, nwk_addr)

    @classmethod
    def dis_dev_addr(cls):
        if db9.llen(ConstDB9.released_addr) != 0:
            nwk_addr = db9.lpop(ConstDB9.released_addr)
            nwk_addr = int(nwk_addr)
            dev_addr = int.to_bytes((NwkID << 25) + nwk_addr, length=4, byteorder='big')
            return dev_addr

        cur_block = db9.get(ConstDB9.current_block)
        if cur_block is None:
            cur_block = 0
        else:
            cur_block = int(cur_block)
        cur_num = db9.get(ConstDB9.current_num)
        if cur_num is None:
            cur_num = 0
        else:
            cur_num = int(cur_num)
        dev_addr = cls.cal_dev_addr(cur_block, cur_num)
        while db0.exists(ConstDB.addr + hexlify(dev_addr).decode()):
            cur_num += 1
            if cur_num == 32:
                cur_block += 1
                cur_num = 0
            dev_addr = cls.cal_dev_addr(cur_block, cur_num)
        db9.set(ConstDB9.current_block, cur_block)
        db9.set(ConstDB9.current_num, cur_num)
        return dev_addr

    @staticmethod
    def cal_dev_addr(cur_block, cur_num):
        addr = (NwkID << 25) + cur_block * (2**5) + cur_num
        try:
            addr_bytes = int.to_bytes(addr, length=4, byteorder='big')
        except OverflowError as e:
            logger.error(
                'error_msg:%s - dev addr have become too big to switch to 4 bytes data - addr=%s block=%s num=%s' %
                (str(e), addr, cur_block, cur_num))
            raise OverflowError
        else:
            return addr_bytes


