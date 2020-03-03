import json
import sys

from tornado import gen
from tornado.httpclient import AsyncHTTPClient
from tornado.options import options

from core.address import Address
from core.exceptions import HTTPConnection
from core.node import Node
from core.utils import CommandType, logger_decorator


# class representing a remote peer
class Remote(Node):
    def __init__(self, address):
        super().__init__(address)
        self.url = f"http://{self.address.ip}:{self.address.port}/chord/"

    @logger_decorator
    async def send(self, msg, retry_limit=4, exit_on_error=True):
        retry_count = 0
        while retry_count < retry_limit:
            try:
                msg['frm'] = f"{options.address}:{options.port}"
                msg['to'] = f'{self.address.ip}:{self.address.port}'
                client = AsyncHTTPClient()
                response = await client.fetch(self.url, method='POST', body=json.dumps(msg))

                response = json.loads(response.body)

                return response
            except Exception:
                await gen.sleep(2 ** retry_count)
                retry_count += 1

        if exit_on_error:
            print('Exiting on error...')
            sys.exit(-1)

        raise HTTPConnection(f'Can not connect to node {self.identifier()} failed.')

    @logger_decorator
    async def ping(self):
        try:
            msg = {'cmd': CommandType.PING}
            await self.send(msg, exit_on_error=False)
            return True

        except HTTPConnection:
            return False

    @logger_decorator
    async def get_successors(self):
        msg = {'cmd': CommandType.GET_SUCCESSORS}
        response = await self.send(msg)

        # if our next guy doesn't have successors, return empty list
        successors = [Remote(Address(node['ip'], node['port'])) for node in response['data']]

        return successors

    @logger_decorator
    async def get_successor(self):
        msg = {'cmd': CommandType.GET_SUCCESSOR}
        response = await self.send(msg)

        return Remote(Address(response['data']['ip'], response['data']['port']))

    @logger_decorator
    async def get_predecessor(self):
        msg = {'cmd': CommandType.GET_PREDECESSOR}
        response = await self.send(msg)

        return Remote(Address(response['data']['ip'], response['data']['port'])) if response['data'] else None

    @logger_decorator
    async def find_successor(self, identifier):
        msg = {'cmd': CommandType.FIND_SUCCESSOR, 'data': {'identifier': identifier}}
        response = await self.send(msg)

        return Remote(Address(response['data']['ip'], response['data']['port']))

    @logger_decorator
    async def get_closest_preceding_finger(self, identifier):
        msg = {'cmd': CommandType.CLOSEST_PRECEDING_FINGER, 'data': {'identifier': identifier}}
        response = await self.send(msg)

        return Remote(Address(response['data']['ip'], response['data']['port']))

    @logger_decorator
    async def notify(self, node):
        cmd = {'cmd': CommandType.NOTIFY, 'data': {'ip': node.address.ip, 'port': node.address.port}}
        await self.send(cmd)

        return True
