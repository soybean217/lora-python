from otaa.main import listen_join_request   # listen_join_request, ListenJoinSuccessThreading

from gevent import monkey; monkey.patch_socket()
import gevent

if __name__ == '__main__':
    gevent.joinall([
        gevent.spawn(listen_join_request),
    ])