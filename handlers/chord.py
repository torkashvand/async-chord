import logging

from handlers.base import JsonHandler

logger = logging.getLogger('play.' + __name__)


class ChordHandler(JsonHandler):

    def initialize(self, node):
        self.node = node

    async def post(self):
        command = self.request.arguments

        self.response = await self.node.execute_command(command)

        return self.write_json()
