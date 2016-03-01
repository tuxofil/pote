"""
Unit test for the Test Storage interface.
"""

import logging
import os
import os.path
import shutil
import time
import unittest

import pote
import pote.tests
pote.tests.REFRESH_PERIOD = 1  # decrease period to one second


logging.basicConfig(level=logging.DEBUG)


class PoteTestStorageTest(unittest.TestCase):
    """
    Unit test for the Test Storage interface.
    """

    path = 'test-storage.tmp'

    def setUp(self):
        """
        Test prepare recipes.
        """
        os.makedirs(self.path)

    def tearDown(self):
        """
        Test destroy recipes.
        """
        shutil.rmtree(self.path)

    def test_unexistent(self):
        """
        Test storage without target directory.
        """
        s = pote.PoteTests(self.path + '-not-exists')
        self.assertMods(s, [])

    def test_discover(self):
        """
        Test modules discover.
        """
        s = pote.PoteTests(self.path)
        self.assertMods(s, [])
        self._populate(['a.py', 'b.py', 'readme', '.py'])
        self.assertMods(s, ['a', 'b'])
        self._populate(['z'])
        self.assertMods(s, [])
        self._populate(['z/__init__.py', 'a/b.py'])
        self.assertMods(s, ['z'])

    def assertMods(self, storage, modules):
        """
        Make assertion for current test list.

        :param storage: interface to the tests storage.
        :type storage: pote.PoteTests

        :param modules: discovered module names
        :type modules: list of strings
        """
        self.assertEqual(sorted(storage.available()), sorted(modules))

    def _populate(self, paths):
        """
        Populate tests directory with files and subdirs.

        :param paths: list of paths relative to tests dir
        :type paths: list of string
        """
        # sleep for a second because some filesystems
        # save mtime up to seconds only.
        time.sleep(1)
        for i in os.listdir(self.path):
            abs_name = os.path.join(self.path, i)
            if os.path.isdir(abs_name):
                shutil.rmtree(abs_name)
            else:
                os.unlink(abs_name)
        for i in paths:
            abs_name = os.path.join(self.path, i)
            dir_name = os.path.dirname(abs_name)
            if not os.path.isdir(dir_name):
                os.makedirs(dir_name)
            with open(abs_name, 'w'):
                pass
