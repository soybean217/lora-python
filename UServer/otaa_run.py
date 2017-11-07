# listen_join_request, ListenJoinSuccessThreading
from otaa.main import listen_join_request
from otaa.main import fresh_cache

from gevent import monkey
monkey.patch_socket()
import gevent

if __name__ == '__main__':
    gevent.joinall([
        gevent.spawn(listen_join_request),
        gevent.spawn(fresh_cache),
    ])
