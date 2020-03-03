from settings import SIZE


class Node:
    def __init__(self, address, remote_address=None):
        self.address = address
        self.remote_address = remote_address

    async def get_successors(self):
        raise NotImplementedError

    async def get_successor(self):
        raise NotImplementedError

    async def get_predecessor(self):
        raise NotImplementedError

    async def find_successor(self, identifier):
        raise NotImplementedError

    async def get_closest_preceding_finger(self, identifier):
        raise NotImplementedError

    async def ping(self):
        raise NotImplementedError

    async def notify(self, node):
        raise NotImplementedError

    def identifier(self, offset=0):
        return (self.address.__hash__() + offset) % SIZE

    def __str__(self):
        return f"{self.address}"

    def __repr__(self):
        return self.__str__()
