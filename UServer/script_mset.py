from database.db0 import db0, ConstDB

keys = db0.keys(ConstDB.msg_up + '*')
print(keys)
for key in keys:
    key_split = key.decode().split(':')
    db0.sadd(ConstDB.mset + key_split[2], key_split[3])

# app_eui = 'ffffffffffffffff'
# dev_eui = 'aa000000000000a1'
# list = db0.sort(ConstDB.mset + dev_eui, by='MSG_UP:' + app_eui + ':' + dev_eui + ':*->rssi')
# for tmst in list:
#     rssi = db0.hgetall(ConstDB.msg_up + app_eui + ':' + dev_eui + ':' + tmst.decode())
#     print(rssi)