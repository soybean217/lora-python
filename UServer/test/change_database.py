import pymysql
import sys
print(sys.path)

from userver.database.db0 import db0, ConstDB
from binascii import unhexlify, hexlify

connection = pymysql.connect(host='localhost',
                             user='nwkserver',
                             password='niotlorasql',
                             db='nwkserver',
                             cursorclass=pymysql.cursors.DictCursor)
cur = connection.cursor()




def sql_hex(byte):
    return '0x' + hexlify(byte).decode()

app_field = ('name', '_Application__token', 'user_id')


def copy_app():
    app_keys = db0.keys(ConstDB.app + '*')
    for app_key in app_keys:
        app_eui = unhexlify(app_key.decode().split(':')[1])
        cur.execute("SELECT * FROM app WHERE app_eui = %s" % sql_hex(app_eui))
        result = cur.fetchall()
        if len(result) > 0:
            print('already added app', result)
        else:
            info = db0.hmget(app_key, app_field)
            name = info[0].decode()
            token = info[1]
            user_id = info[2].decode()
            sql = "INSERT INTO app (app_eui, name, token, user_id) VALUES (%s,'%s',%s,%s);" \
                  % (sql_hex(app_eui), name, sql_hex(token), user_id)
            print(sql)
            cur.execute(sql)
            connection.commit()
            print(result)


gateway_field = ('name', 'user_id')


def copy_gateway():
    gateway_keys = db0.keys(ConstDB.gateway + '*')
    for gateway_key in gateway_keys:
        gateway_id = unhexlify(gateway_key.decode().split(':')[1])
        cur.execute("SELECT * FROM gateway WHERE id = %s" % sql_hex(gateway_id))
        result = cur.fetchall()
        if len(result) > 0:
            print('already added gateway', result)
        else:
            info = db0.hmget(gateway_key, gateway_field)
            name = info[0].decode()
            user_id = info[1].decode()
            sql = "INSERT INTO gateway (id, name, user_id) VALUES (%s,'%s',%s);" \
                  % (sql_hex(gateway_id), name, user_id)
            print(sql)
            cur.execute(sql)
            connection.commit()


def clear_redis_app():
    app_keys = db0.keys(ConstDB.app + '*')
    for app_key in app_keys:
        db0.hdel(app_key, 'name', '_Application__token')


def clear_redis_gateway():
    gateway_keys = db0.keys(ConstDB.gateway + '*')
    for key in gateway_keys:
        db0.hdel(key, 'name')

if __name__ == '__main__':
    copy_app()
    copy_gateway()
    clear_redis_app()
    clear_redis_gateway()