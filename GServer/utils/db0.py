import redis
from config import RedisHost, RedisPasswd, RedisPort

db0 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=10, password=RedisPasswd)


class Channel0:
    msg_alarm = 'msg_alarm:'
    up_alarm = 'up_alarm:'
    dn_alarm = 'dn_alarm:'
    que_down_alarm_c = 'que_down_alarm_c:'
    que_down_alarm_b = 'que_down_alarm_b:'
    que_down_alarm_multi = 'que_down_alarm_multi:'
    rx1_alarm = 'rx1_alarm:'


class ConstDB0:
    asserterror_fcnt_error = "AssertError: fcnt error: "
    asserterror_fcnt_up_overflow = "AssertError: fcnt_up overflow: "

    dev = 'DEV:'
    dev_info = 'INFO_DEV:'
    app = 'APP:'

    class_b = 'B:'
    b_time = 'B_TIME:'

    app_groups = 'GROUPS_APP:'

    addr = 'ADDR:'

    gateway = 'GATEWAY:'
    dev_gateways = 'GATEWAYS_DEV:'
    trans_params = 'TRANS_DEV:'

    group = 'GROUP:'
    group_dev = 'DEV_GROUP:'

    gateway_pull = 'GATEWAY_PULL:'

    resend = 'RESEND:'

    msg_up = 'MSG_UP:'
    msg_down = 'MSG_DOWN:'
    msg_down_multi = 'MSG_DOWN_M:'
    mset = 'MSET:'

    que_down = 'QUE_DOWN:'

    mac_cmd_que = 'QUE_MAC_CMD:'
    mac_cmd = 'MAC_CMD:'

    dev_ack = 'ACK_DEV:'

    statistics_up = 'STATISTICS_UP:'
    statistics_down = 'STATISTICS_DOWN:'
    statistics_retrans = 'STATISTICS_RETRANS:'

    statistics_freq = 'STATISTICS_FREQ:'

    app_eui = 'app_eui'

    niot_request = 'NIOT:REQUEST:'


