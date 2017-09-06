from uuid import getnode

mac = getnode()
MAC = ':'.join(("%012X" % mac)[i:i+2] for i in range(0, 12, 2))
MACSERVER = 'E4:1F:13:1C:67:54'  # Server mac address of bond0

if MAC == MACSERVER:
    # server side
    HOST = '183.230.40.231'
    # HOST = 'localhost'
    SOCKET = '?unix_socket=/data/mysql5.6/mysql.sock'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://pro_nwkserver:niotlorasql@localhost:3312/nwkserver' + SOCKET
    SQLALCHEMY_BINDS = {'lorawan': 'mysql+pymysql://pro_lorawan:niotlorasql@localhost:3312/lorawan' + SOCKET,}

    RedisPort = 6380
else:
    # local side
    HOST = '127.0.0.1'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://nwkserver:niotlorasql@localhost:3306/nwkserver'
    SQLALCHEMY_BINDS = {'lorawan': 'mysql+pymysql://lorawan:niotlorasql@localhost:3306/lorawan',}

    RedisPort = 6379

RedisHost = '127.0.0.1'
RedisPasswd = 'niotloraredis'

FRONT_END_BASE_URL = 'http://' + HOST + ':8888/#'

# Flask settings
SECRET_KEY = 'top-secret-confidential'
# SECRET_KEY = 'gjr39dkjn344_!67#'
CSRF_ENABLED = False

# Flask-Mail settings
# MAIL_USERNAME = 'lorawan@cniotroot.cn'
MAIL_USERNAME = 'lorawan@cnicg.cn'
MAIL_PASSWORD = 'niot1234'
# MAIL_DEFAULT_SENDER = '"LoRaWAN" <lorawan@cniotroot.cn>'
MAIL_DEFAULT_SENDER = '"LoRaWAN" <lorawan@cnicg.cn>'
MAIL_SERVER = 'mail.cstnet.cn'
MAIL_PORT = '465'
MAIL_USE_SSL = True

OAUTH2_PROVIDER_TOKEN_EXPIRES_IN = 10

"""
smtp connection error check mail server mail port
"""

APP_NAME = "LoRaWAN"                # Used by email templates

