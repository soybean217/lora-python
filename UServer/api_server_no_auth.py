from gevent import monkey
monkey.patch_all()
from http_api_no_auth import create_api_server
from userver.database.db_sql import db_sql
app = create_api_server('config')
app.debug = True


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_sql.session.remove()



from gevent.wsgi import WSGIServer

if __name__ == '__main__':
    http_api = WSGIServer((app.config['HOST'], 8109), app)
    http_api.serve_forever()
# app.run(host=app.config['HOST'], port=8108)
