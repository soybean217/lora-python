# listen_join_request, ListenJoinSuccessThreading
from jingyi.main import listen_jingyi_request
from jingyi.main import heartbeat_jingyi

from gevent import monkey
monkey.patch_socket()
import gevent

if __name__ == '__main__':
    gevent.joinall([
        gevent.spawn(heartbeat_jingyi),
        gevent.spawn(listen_jingyi_request),
    ])
