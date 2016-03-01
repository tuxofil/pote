"""
Python Online Test Executor core library.
"""

import logging
import os.path

from .archive import PoteArchive
from .rest import PoteApiServer
from .tests import PoteTests
from .scheduler import PoteScheduler


LOGGER = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Default values

DEF_BINDADDR = '127.0.0.1'  # default interface to listen to
DEF_BINDPORT = 8901  # default TCP port number to listen to
DEF_ENVOS_COUNT = 3
DEF_ENVOS_PATH = '/var/lib/pote/envos'
DEF_TESTS_PATH = '/usr/share/pote/tests'
DEF_QUEUE_PATH = '/var/lib/pote/queue'
DEF_ARCHIVE_PATH = '/var/lib/pote/archive'


def start_server(bindaddr=None, bindport=None, envos_count=None,
                 envos_path=None, tests_path=None, queue_path=None,
                 archive_path=None):
    """
    Start Pote server.

    :param envos: how many environments to use.
    :type envos: integer
    """
    # Apply defaults
    if bindaddr is None:
        bindaddr = DEF_BINDADDR
    if bindport is None:
        bindport = DEF_BINDPORT
    if envos_count is None:
        envos_count = DEF_ENVOS_COUNT
    if envos_path is None:
        envos_path = DEF_ENVOS_PATH
    if tests_path is None:
        tests_path = DEF_TESTS_PATH
    if queue_path is None:
        queue_path = DEF_QUEUE_PATH
    if archive_path is None:
        archive_path = DEF_ARCHIVE_PATH
    LOGGER.info('starting...')
    # initialize archive storage
    archive = PoteArchive(archive_path)
    # create interface to the tests storage
    tests = PoteTests(tests_path)
    # spawn Scheduler thread
    scheduler = PoteScheduler(envos_count, envos_path,
                              queue_path, tests, archive)
    scheduler.start()
    # start RESTful httpd
    rest_server = PoteApiServer(bindaddr, bindport, scheduler,
                                tests, archive)
    rest_server.serve_forever()
