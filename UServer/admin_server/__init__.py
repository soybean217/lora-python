

def http_server():
    from gevent import monkey
    monkey.patch_all()
    from admin_server.admin_http_api import create_api_server
    from database.db_sql import db_sql
    app = create_api_server('config')
    app.debug = True

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_sql.session.remove()

    from gevent.wsgi import WSGIServer

    # if __name__ == '__main__':
    http_api = WSGIServer((app.config['HOST'], 10008), app)
    http_api.serve_forever()
    # app.run(host=app.config['HOST'], port=8108)


def data_server():
    from admin_server.admin_data_update import main
    # import gevent
    # from gevent import monkey;monkey.patch_all()
    main()
    # gevent.joinall([gevent.spawn(main), ])
