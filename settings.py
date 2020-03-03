import logging
import os

import tornado
import tornado.template
from environs import Env
from tornado.options import define, options

import environment
import logconfig

env = Env()
env.read_env()  # read .env file, if it exists

########
# log size of the ring
LOGSIZE = 3
SIZE = 1 << LOGSIZE

# successors list size (to continue operating on node failures)
NUMBER_OF_SUCCESSORS = 4

# Stabilize
STABILIZE_INTERVAL = 1

# Fix Fingers
FIX_FINGERS_INTERVAL = 4

# Update Successors
UPDATE_SUCCESSORS_INTERVAL = 1
########


# Make filepaths relative to settings.
path = lambda root, *a: os.path.join(root, *a)
ROOT = os.path.dirname(os.path.abspath(__file__))

define("address", default='127.0.0.1', help="run on the given port", type=int)
define("port", default=9000, help="run on the given port", type=int)
define("config", default=None, help="tornado config file")
define("debug", default=True, help="debug mode")
define("bootstrap_address", default='127.0.0.1', help="bootstrap node address")
define("bootstrap_port", default='9000', help="bootstrap node port")
define("is_bootstrap", default=False, help="a bootstrapping node")
define("show_more", default=False, help="a bootstrapping node")

tornado.options.parse_command_line()

MEDIA_ROOT = path(ROOT, 'media')
TEMPLATE_ROOT = path(ROOT, 'templates')

# Deployment Configuration


DEBUG = env.bool('TORNADO_DEBUG', default=False)

settings = {}
settings['debug'] = DEBUG
settings['static_path'] = MEDIA_ROOT
settings['cookie_secret'] = env('TORNADO_COOKIE_SECRET', "U4PqmJPsCWEq2PDSSZFYt")
settings['xsrf_cookies'] = False
settings['template_loader'] = tornado.template.Loader(TEMPLATE_ROOT)
settings['autoreload'] = DEBUG
settings['serve_traceback'] = DEBUG

SYSLOG_TAG = "play"
SYSLOG_FACILITY = logging.handlers.SysLogHandler.LOG_LOCAL2

# See PEP 391 and logconfig for formatting help.  Each section of LOGGERS
# will get merged into the corresponding section of log_settings.py.
# Handlers and log levels are set up automatically based on LOG_LEVEL and DEBUG
# unless you set them here.  Messages will not propagate through a logger
# unless propagate: True is set.
LOGGERS = {
    'loggers': {
        'play': {},
    },
}

if settings['debug']:
    LOG_LEVEL = logging.DEBUG
else:
    LOG_LEVEL = logging.INFO

USE_SYSLOG = True

logconfig.initialize_logging(SYSLOG_TAG, SYSLOG_FACILITY, LOGGERS, LOG_LEVEL, USE_SYSLOG)

if options.config:
    tornado.options.parse_config_file(options.config)
