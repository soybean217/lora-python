from gevent import monkey
monkey.patch_all()
from http_api_oauth import create_api_server
from database.db_sql import db_sql
app = create_api_server('config')
app.debug = True


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_sql.session.remove()


from gevent.wsgi import WSGIServer

if __name__ == '__main__':
    http_api = WSGIServer(('', 8108), app)
    http_api.serve_forever()
# app.run(host=app.config['HOST'], port=8108)
app.run(port=8108)