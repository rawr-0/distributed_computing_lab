import tornado.web
from tornado import httpserver as hs
from tornado import httpclient as hc
import threading
import asyncio

from tornado.netutil import bind_sockets


class Chain:
    def __init__(self, name, port):
        self.name = name
        self.port = port
        self.nowserver = None
        self.network = []
        self.pos = 0
        self.httpclient = hc.HTTPClient()

        self.score = 0

    def main(self):
        threading.Thread(target=asyncio.run,args=(self.server(),)).start()
        self.client()

    def client(self):
        self.add_first_node()
        while True:
            self.update_info(self.httpclient)
            if not self.check_connection(self.httpclient):
                self.pos += 1
                self.nowserver = self.network[self.pos]
                print("server died")
                print(f"connect to {self.nowserver}")
            print(self.network)

    async def server(self):
        await self.sub_serv()
        await asyncio.Event().wait()

    async def sub_serv(self):
        app = tornado.web.Application(handlers = [
            (r"/", BaseHandler),
            (r"/update", SecondHandler)])
        app.network = self.network
        app.chain = self
        server = hs.HTTPServer(app)
        sockets = bind_sockets(self.port)
        server.add_sockets(sockets)

    def add_first_node(self):
        if len(self.network) == 0:
            print("add first node to connect:")
            self.network.append(str(input()))
            # http://localhost:8888
            self.nowserver = self.network[self.pos]
            self.update_connection(self.httpclient)

    def update_connection(self, http_client):
        try:
            response = http_client.fetch(self.nowserver, method="POST", body=f"http://localhost:{self.port}".encode())
        except Exception as e:
            print("Error: %s" % e)
        else:
            for i in response.body.decode().split(sep=','):
                if self.network.count(i) == 0 and i != '':
                    self.network.append(i)

    def update_info(self, http_client):
        try:
            response = http_client.fetch(f"{self.nowserver}/update", method="GET")
        except Exception as e:
            print("Error: %s" % e)
        else:
            for i in response.body.decode().split(sep=','):
                if self.network.count(i) == 0 and i != '':
                    self.network.append(i)

    def check_connection(self, http_client):
        try:
            http_client.fetch(self.nowserver, method="GET")
        except Exception:
            return False
        else:
            return True

    def client_check_update(self):
        self.update_connection(self.httpclient)

    def message(self, info):
        print(info)


class BaseHandler(tornado.web.RequestHandler):
    def post(self):
        if self.application.chain.nowserver != self.request.body.decode():
            self.application.chain.network.append(self.request.body.decode())
        for i in self.application.network:
            self.write(f"{i},")

    def get(self):
        self.write("alive")


class SecondHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.chain.nowserver != f"http://localhost:{self.application.chain.port}":
            self.application.chain.update_info(self.application.chain.httpclient)
        for i in self.application.network:
            self.write(f"{i},")

