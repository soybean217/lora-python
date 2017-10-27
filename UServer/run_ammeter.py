# listen_join_request, ListenJoinSuccessThreading
from ammeter.main import listen_ammeter_request
from ammeter.main import test_post
import threading
from gevent import monkey
monkey.patch_socket()
import gevent

if __name__ == '__main__':
    # gevent.joinall([
    #     # gevent.spawn(listen_ammeter_request),
    #     gevent.spawn(test_post),
    # ])
    threads = []
    # threads.append(threading.Thread(target=test_post))
    threads.append(threading.Thread(target=listen_ammeter_request))
    for t in threads:
        t.start()
