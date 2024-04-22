from server import Server


if __name__ == '__main__':
    # set config 
    server = Server('0.0.0.0', 8080)

    # init routes
    server.init_routes()

    server.run()
