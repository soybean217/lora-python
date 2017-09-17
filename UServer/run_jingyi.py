# listen_join_request, ListenJoinSuccessThreading
from jingyi.main import listen_jingyi_request
from jingyi.main import heartbeat_jingyi
from jingyi.main import loop_sensor_jingyi
import threading
from gevent import monkey
monkey.patch_socket()
import gevent

if __name__ == '__main__':
    # gevent.joinall([
    #     gevent.spawn(heartbeat_jingyi),
    #     gevent.spawn(listen_jingyi_request),
    # ])
    threads = []
    threads.append(threading.Thread(target=heartbeat_jingyi))
    threads.append(threading.Thread(target=listen_jingyi_request))
    threads.append(threading.Thread(target=loop_sensor_jingyi))
    for t in threads:
        t.start()
