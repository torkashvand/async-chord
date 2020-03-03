import functools

from tornado.options import options

from settings import SIZE


# Helper function to determine if a key falls within a range
def is_in_range(c, a, b):
    # is c in [a,b)?, if a == b then it assumes a full circle
    # on the DHT, so it returns True.
    a = a % SIZE
    b = b % SIZE
    c = c % SIZE

    if a < b:
        return a <= c < b

    return a <= c or c < b


class CommandType:
    # just for ease of debugging I use this verbose name
    GET_SUCCESSOR = 'GET_SUCCESSOR'
    FIND_SUCCESSOR = 'FIND_SUCCESSOR'
    GET_PREDECESSOR = 'GET_PREDECESSOR'
    CLOSEST_PRECEDING_FINGER = 'CLOSEST_PRECEDING_FINGER'
    NOTIFY = 'NOTIFY'
    GET_SUCCESSORS = 'GET_SUCCESSORS'
    PING = 'PING'


def logger_decorator(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        try:

            if options.show_more:

                print(f'[{self}] -> {func.__qualname__}({args} {kwargs})')

                result = await func(self, *args, **kwargs)

                print(f'[{self}] -> {func.__qualname__}({args} {kwargs}) -> {result}')
            else:
                result = await func(self, *args, **kwargs)

            return result
        except Exception as e:
            print(f'Exception: {e}')

    return wrapper
