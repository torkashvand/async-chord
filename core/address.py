import hashlib

from settings import SIZE


class Address:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def __key(self):
        return f"{self.ip}{self.port}".encode()

    def __hash__(self):
        """
        Python uses a random hash seed to prevent attackers from tar-pitting your application by sending you keys
        designed to collide. to prevent changing hash code for this test project I use this method.
        """
        m = hashlib.sha256()
        m.update(self.__key())
        return int(m.hexdigest(), 16) % SIZE

    def __eq__(self, other):
        if isinstance(other, Address):
            return self.__key() == other.__key()

        return NotImplemented

    def __lt__(self, other):
        return self.__hash__() < other.__hash__()

    def __gt__(self, other):
        return self.__hash__() > other.__hash__()

    def __le__(self, other):
        return self.__hash__() <= other.__hash__()

    def __ge__(self, other):
        return self.__hash__() >= other.__hash__()

    def __str__(self):
        return f'{self.ip}:{self.port}'

    def __repr__(self):
        return self.__str__()


for port in range(9000, 9020):
    print(f"{port} -> {Address('127.0.0.1', port).__hash__()}")
