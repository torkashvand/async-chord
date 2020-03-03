import asyncio
import sys
import threading
import time
from random import randrange

import tornado
from tornado import httpserver
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase, gen_test

from app import PlayStackTornado
from core.address import Address
from core.local import Local
from core.utils import is_in_range
from settings import SIZE


# thread to run Local's run method
class TornadoThread(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.node = node

    def run(self):
        print(f'Starting application on port: {self.node.address.port}')
        asyncio.set_event_loop(asyncio.new_event_loop())

        app = PlayStackTornado(node=self.node)
        http_server_api = httpserver.HTTPServer(app)
        http_server_api.listen(self.node.address.port)
        self.node.start()
        time.sleep(1)
        IOLoop.instance().start()

    @staticmethod
    def stop_io_loop():
        tornado.ioloop.IOLoop.instance().stop()


class MyTestCase(AsyncHTTPTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # create addresses
        cls.address_list = []
        port_list = [9065, 9081, 9074, 9087, 9085, 9118, 9117, 9897, 9120, 9103, 9107, 9108, 9192, 9203, 9204, 9212]
        for port in port_list:
            cls.address_list.append(Address(ip='127.0.0.1', port=port))

        # keep unique ones
        address_list = sorted(set(cls.address_list))

        # hash the addresses
        cls.hash_list = [addr.__hash__() for addr in address_list]
        cls.hash_list.sort()

        # create the nodes
        cls.peers = []
        cls.server_list = []
        for i in range(0, len(address_list)):
            if i == 0:
                local = Local(address_list[i])
            else:
                # use a first already created peer's address as the remote for bootstrapping
                local = Local(address_list[i], cls.peers[0].address)

            app = TornadoThread(node=local)
            app.start()
            cls.server_list.append(app)

            cls.peers.append(local)

    def get_new_ioloop(self):
        return IOLoop.current()

    def get_app(self):
        local = Local(Address(ip='127.0.0.1', port=9000))
        return TornadoThread(node=local)

    @gen_test
    async def test_key_lookup(self):
        """Running key lookup consistency test"""

        for key in range(SIZE):
            # select random node
            node = self.peers[randrange(len(self.peers))]

            # get the successor
            target = await node.find_successor(key)

            for i in range(len(self.peers)):
                if is_in_range(key, self.hash_list[i] + 1, self.hash_list[(i + 1) % len(self.peers)] + 1):
                    try:
                        assert target.identifier() == self.hash_list[(i + 1) % len(self.peers)]
                    except Exception:
                        for app in self.server_list:
                            app.stop_io_loop()

                        sys.exit()


if __name__ == '__main__':
    import unittest

    unittest.main()
