from socket_io import create_app, socketio

app = create_app('config')
app.debug = True

if __name__ == '__main__':
    socketio.run(app, host=app.config['HOST'], port=8100)