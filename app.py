#!/usr/bin/env python

import tornado.httpserver
import tornado.web
from tornado.ioloop import IOLoop
from tornado.options import options

from core.address import Address
from core.local import Local
from handlers.chord import ChordHandler
from settings import settings
from urls import url_patterns


class PlayStackTornado(tornado.web.Application):
    def __init__(self, node):
        url_patterns.append((r"/chord/", ChordHandler, {'node': node}))
        tornado.web.Application.__init__(self, url_patterns, **settings)


def main():
    if options.is_bootstrap:
        node = Local(Address(ip=options.address, port=options.port))
    else:
        node = Local(Address(ip=options.address, port=options.port),
                     Address(ip=options.bootstrap_address, port=options.bootstrap_port))

    app = PlayStackTornado(node=node)
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port)
    node.start()
    IOLoop.current().start()


if __name__ == "__main__":
    main()
