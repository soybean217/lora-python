import redis


class ConstDB:
    app = 'APP:'
    app_devs = 'DEVS_APP:'
    app_groups = 'GROUPS_APP:'

    b = 'B:'

    gateway = 'GATEWAY:'
    gateway_pull = 'GATEWAY_PULL:'

    dev = 'DEV:'
    addr = 'ADDR:'
    dev_status = 'DEV_STATUS:'

    dev_info = 'INFO_DEV:'

    trans_params = 'TRANS_DEV:'
    dev_gateways = 'GATEWAYS_DEV:'

    group = 'GROUP:'
    group_dev = 'DEV_GROUP:'

    msg_up = 'MSG_UP:'
    msg_down = 'MSG_DOWN:'
    msg_down_multi = 'MSG_DOWN_M:'

    que_down = 'QUE_DOWN:'

    mac_cmd_que = 'QUE_MAC_CMD:'
    mac_cmd = 'MAC_CMD:'

    dev_ack = 'ACK_DEV:'

    statistics_up = 'STATISTICS_UP:'
    statistics_down = 'STATISTICS_DOWN:'
    statistics_freq = 'STATISTICS_FREQ:'


class Channel:
    msg_alarm = 'msg_alarm:'
    que_down_alarm_c = 'que_down_alarm_c:'
    que_down_alarm_b = 'que_down_alarm_b:'
    que_down_alarm_multi = 'que_down_alarm_multi:'


class RedisDBConfig:
    HOST = '127.0.0.1'
    PORT = 6379
    DBID = 10
    PASSWORD = 'niotloraredis'

# connection_pool = redis.ConnectionPool(host=RedisDBConfig.HOST,
#                          port=RedisDBConfig.PORT,
#                          password=RedisDBConfig.PASSWORD,
#                          db=RedisDBConfig.DBID)

db0 = redis.StrictRedis(host=RedisDBConfig.HOST,
                        port=RedisDBConfig.PORT,
                        password=RedisDBConfig.PASSWORD,
                        db=RedisDBConfig.DBID)
# db0 = redis.Redis(connection_pool=connection_pool)