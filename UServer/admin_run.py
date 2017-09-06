import sys
from utils.log import Logger

if __name__ == '__main__':
    input_argv = sys.argv
    try:
        server_name = input_argv[1]
        if server_name == 'http_server':
            from admin_server import http_server
            Logger.info('Admin Http Server Begin to run')
            http_server()
        elif server_name == 'data_server':
            from admin_server import data_server
            Logger.info('Admin Data Server Begin to run')
            data_server()
        else:
            print('do not understand the command:%s.' % server_name)
    except IndexError as e:
        print('need input argv')