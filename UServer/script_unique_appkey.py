import uuid
# from binascii import unhexlify, hexlify
# a = uuid.UUID(bytes=unhexlify('2B7E151628AED2A6ABF7158809CF4F3C'))
# b = uuid.uuid5(uuid.NAMESPACE_DNS, '2B7E151628AED2A6ABF7158809CF4F3C')
# print(hexlify(b.bytes))
# print(b)
import pymysql
from binascii import hexlify
import uuid


def generate_random_token():
    return uuid.uuid4().bytes


connection = pymysql.connect(host='localhost',
                             user='nwkserver',
                             password='niotlorasql',
                             db='nwkserver')

try:
    with connection.cursor() as cursor:
        # Create a new record
        sql = "SELECT dev_eui, appkey FROM join_device where appkey in (SELECT appkey from join_device group by appkey having count(*) > 1);"
        cursor.execute(sql)
        # rows = cursor.fetchall()
        while True:
            row = cursor.fetchone()
            print(row)
            if row is not None:
                print(0, row)
                change_sql = "UPDATE join_device SET appkey = X'" + hexlify(generate_random_token()).decode() + "' WHERE dev_eui = X'" + hexlify(row[0]).decode() + "';"
                print(change_sql)
                with connection.cursor() as other_cursor:
                    result = other_cursor.execute(change_sql)
                    print(1, result)
            else:
                break
        connection.commit()

finally:
    connection.close()