import json
import logging

import tornado.web
import tornado.web

logger = logging.getLogger('boilerplate.' + __name__)


class JsonHandler(tornado.web.RequestHandler):
    """Request handler where requests and responses speak JSON."""
    node = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set up response dictionary.
        self.response = dict()

    def prepare(self):
        # Incorporate request JSON into arguments dictionary.
        if self.request.body:
            try:
                json_data = json.loads(self.request.body)
                self.request.arguments = json_data
            except ValueError:
                message = 'Unable to parse JSON.'
                self.send_error(400, message=message)  # Bad Request

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')

    def write_error(self, status_code, **kwargs):
        if 'message' not in kwargs:
            if status_code == 405:
                kwargs['message'] = 'Invalid HTTP method.'
            else:
                kwargs['message'] = 'Unknown error.'

        self.response = kwargs

        self.write_json()

    def write_json(self):
        output = json.dumps(self.response)
        self.write(output)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("base.html", title="PubSub + WebSocket Demo")
