"""
Interface to tests storage.
"""

import logging
import os
import os.path
import time


REFRESH_PERIOD = 60  # 1 minute


class PoteTests(object):
    """
    Main interface to the Storage
    """

    def __init__(self, path):
        """
        Constructor.

        :param path: path to a directory with tests.
        :type path: string
        """
        self.tests = None
        self.last_updated = 0
        self.logger = logging.getLogger(self.__class__.__name__)
        self.path = os.path.abspath(path)
        self.logger.debug('started at %r', self.path)

    def available(self):
        """
        Return list of python module names of available tests.

        :rtype: list of string
        """
        if time.time() > self.last_updated + REFRESH_PERIOD:
            self.logger.debug('outdated. rediscovering...')
            self._update()
        return self.tests

    def __contains__(self, name):
        """
        Return True if given name is a valid test module name.

        :param name: python module name
        :type name: string

        :rtype: boolean
        """
        return name in self.available()

    def _update(self):
        """
        Conditionally re-read tests from the tests directory.
        """
        if not os.path.isdir(self.path):
            self.logger.warning('no such directory: %r', self.path)
            self.tests = []
            self.last_updated = time.time()
            return
        tests = []
        for name in os.listdir(self.path):
            abs_name = os.path.join(self.path, name)
            if os.path.isfile(abs_name):
                py_ext = '.py'
                if (not name.startswith('.')) and name.endswith(py_ext):
                    self.logger.debug('found normal module: %r', name)
                    tests.append(name[:-len(py_ext)])
            elif os.path.isdir(abs_name):
                if os.path.isfile(os.path.join(abs_name, '__init__.py')):
                    self.logger.debug('python package found: %r', name)
                    tests.append(name)
        self.last_updated = time.time()
        self.tests = tests
