from .server import Server


if __name__ == '__main__':
    # set config 
    server = Server('127.0.0.1', 8090)

    server.init_routes()

    server.run()