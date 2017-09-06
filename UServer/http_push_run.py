from http_push.main import listen_msg

from gevent import monkey; monkey.patch_all()
import gevent


if __name__ == '__main__':
    gevent.joinall([
        gevent.spawn(listen_msg),
    ])
