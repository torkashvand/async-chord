import logging
import random
import sys

from tornado import gen
from tornado.ioloop import IOLoop

from core.address import Address
from core.node import Node
from core.remote import Remote
from core.utils import CommandType, is_in_range, logger_decorator
from settings import (FIX_FINGERS_INTERVAL, STABILIZE_INTERVAL, UPDATE_SUCCESSORS_INTERVAL, LOGSIZE,
                      NUMBER_OF_SUCCESSORS)


# class representing a local peer
class Local(Node):
    def __init__(self, address, remote_address=None):
        super().__init__(address)
        # list of successors
        self.successors = []
        # initially just set successor
        self.finger = [None for _ in range(LOGSIZE)]
        self.predecessor = None
        self.remote_address = remote_address

    def start(self):
        # join the DHT
        IOLoop.current().add_callback(self.join, self.remote_address)

    @logger_decorator
    async def join(self, remote_address=None):
        if remote_address:
            remote = Remote(remote_address)
            self.finger[0] = await remote.find_successor(self.identifier())
        else:
            self.finger[0] = self

        logging.info(f'{self.address} with id ({self.identifier()}) joined.')

        # start the daemons
        IOLoop.current().add_callback(self.stabilize)
        IOLoop.current().add_callback(self.fix_fingers)
        IOLoop.current().add_callback(self.update_successors)

    @logger_decorator
    async def stabilize(self):
        while True:
            successor = await self.get_successor()

            # We may have found that x is our new successor if
            # - x = pred(successor(n))
            # - x exists
            # - x is in range (n, successor(n))
            # - [n+1, successor(n)) is non-empty
            # fix finger[0] if successor failed
            if successor.identifier() != self.finger[0].identifier():
                self.finger[0] = successor

            predecessor = await successor.get_predecessor()

            if predecessor:
                in_range = is_in_range(predecessor.identifier(), self.identifier(1), successor.identifier())

                if in_range and self.identifier(1) != successor.identifier() and await predecessor.ping():
                    self.finger[0] = predecessor

            # We notify our new successor about us
            successor = await self.get_successor()

            logging.info(f'new successor is -> {successor.identifier()}')

            await successor.notify(self)
            await gen.sleep(STABILIZE_INTERVAL)

    @logger_decorator
    async def fix_fingers(self):
        while True:
            # Randomly select an entry in finger table and update its value
            # Finger i points to successor of n+2**i
            i = random.randrange(LOGSIZE - 1) + 1
            self.finger[i] = await self.find_successor(self.identifier(1 << i))

            for_print = ', '.join([f"{n.identifier()}" for n in self.finger if n])
            logging.info(f'finger table for node "{self.identifier()}" is -> [{for_print}]')

            await gen.sleep(FIX_FINGERS_INTERVAL)

    @logger_decorator
    async def update_successors(self):
        while True:
            successor = await self.get_successor()

            # if we are not alone in the ring, calculate
            if successor.identifier() != self.identifier():
                successor_list = await successor.get_successors()
                self.successors = [successor] + successor_list

            for_print = ', '.join([f"{n.identifier()}" for n in self.successors])
            logging.info(f'successor list for node "{self.identifier()}" is -> [{for_print}]')

            await gen.sleep(UPDATE_SUCCESSORS_INTERVAL)

    @logger_decorator
    async def execute_command(self, command):
        cmd = command['cmd']
        data = command.get('data')

        result = dict(data=None)
        if cmd == CommandType.GET_SUCCESSOR:
            successor = await self.get_successor()
            result['data'] = {'ip': successor.address.ip, 'port': successor.address.port}

        elif cmd == CommandType.GET_PREDECESSOR:
            # we can only reply if we have a predecessor
            if self.predecessor:
                result['data'] = {'ip': self.predecessor.address.ip, 'port': self.predecessor.address.port}

        elif cmd == CommandType.FIND_SUCCESSOR:
            successor = await self.find_successor(data['identifier'])
            result['data'] = {'ip': successor.address.ip, 'port': successor.address.port}

        elif cmd == CommandType.CLOSEST_PRECEDING_FINGER:
            closest = await self.get_closest_preceding_finger(data['identifier'])
            result['data'] = {'ip': closest.address.ip, 'port': closest.address.port}

        elif cmd == CommandType.NOTIFY:
            await self.notify(Remote(Address(data['ip'], data['port'])))

        elif cmd == CommandType.GET_SUCCESSORS:
            result['data'] = await self.get_successors()

        elif cmd == CommandType.PING:
            result['data'] = True

        return result

    @logger_decorator
    async def ping(self):
        return True

    @logger_decorator
    async def notify(self, remote):
        # Someone thinks they are our predecessor, they are if
        # - we don't have a predecessor
        # OR
        # - the new node `remote` is in the range (pred(n), n)
        # OR
        # - our previous predecessor is dead

        if not await self.get_predecessor():
            self.predecessor = remote
        else:
            predecessor = await self.get_predecessor()
            in_range = is_in_range(remote.identifier(), predecessor.identifier(1), self.identifier())

            if in_range:
                self.predecessor = remote

    @logger_decorator
    async def get_successors(self):
        s = [{'ip': node.address.ip, 'port': node.address.port} for node in self.successors[:NUMBER_OF_SUCCESSORS - 1]]

        return s

    @logger_decorator
    async def get_successor(self):
        # We make sure to return an existing successor, there `might`
        # be redundancy between finger[0] and successors[0], but
        # it doesn't harm
        for remote in [self.finger[0]] + self.successors:
            connected = await remote.ping()

            if connected:
                self.finger[0] = remote
                return remote

        print("No successor available, aborting")
        sys.exit(-1)

    @logger_decorator
    async def get_predecessor(self):
        return self.predecessor

    @logger_decorator
    async def find_successor(self, identifier):
        # The successor of a key can be us if
        # - we have a pred(n)
        # - identifier is in (pred(n), n]
        predecessor = await self.get_predecessor()
        if predecessor and is_in_range(identifier, predecessor.identifier(1), self.identifier(1)):
            return self

        node = await self.find_predecessor(identifier)

        return await node.get_successor()

    @logger_decorator
    async def find_predecessor(self, identifier):
        node = self

        # If we are alone in the ring, we are the pred(identifier)
        successor = await node.get_successor()
        if successor.identifier() == node.identifier():
            return node

        successor = await node.get_successor()
        while not is_in_range(identifier, node.identifier(1), successor.identifier(1)):
            successor = await node.get_successor()
            node = await node.get_closest_preceding_finger(identifier)

        return node

    @logger_decorator
    async def get_closest_preceding_finger(self, identifier):
        # first fingers in decreasing distance, then successors in
        # increasing distance.
        for remote in reversed(self.successors + self.finger):
            if remote and is_in_range(remote.identifier(), self.identifier(1), identifier) and await remote.ping():
                return remote

        return self
