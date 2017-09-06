import redis
from time import sleep

db0 = redis.StrictRedis(host='127.0.0.1',
                        port=6379,
                        password='niotloraredis',
                        db=10)


def run():
    while True:
        sleep(30)
        for client in db0.client_list():
            if client['cmd'] == 'unsubscribe':
                db0.execute_command('client', 'kill', 'id', client['id'])
                print('CLIENT KILL ID %s' % client['id'])

if __name__ == '__main__':
    run()