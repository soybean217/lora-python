import redis
from config import RedisHost, RedisPasswd, RedisPort

db2 = redis.StrictRedis(host=RedisHost, port=RedisPort, db=2, password=RedisPasswd)


class ConstDB2:
    up_m = 'UP_M:'
    dn_m = 'DN_M:'

    up_l = 'UP_L:'
    up_t = 'UP_T:'
    dn_t = 'DN_T:'
    up_l_l = 'UP_L_L:'
    up_gateway = 'UP_GW:'
    dn_gateway = 'DN_GW:'
    up_cur_l = 'UP_CUR_L:'

    up_gw_s = 'UP_GW_S:'

