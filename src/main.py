from server import Server


if __name__ == '__main__':
    # set config 
    server = Server('0.0.0.0', 8080)

    server.init_routes()

    server.run()