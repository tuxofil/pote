"""
Unit test for the Job Archive Storage interface.
"""

import logging
import os
import os.path
import shutil
import time
import unittest

import pote


logging.basicConfig(level=logging.DEBUG)


class PoteArchiveTest(unittest.TestCase):
    """
    Unit test for the Job Archive Storage interface.
    """

    path = 'archive-storage.tmp'

    def setUp(self):
        """
        Test prepare recipes.
        """
        pass

    def tearDown(self):
        """
        Test destroy recipes.
        """
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)

    def test_unexistent(self):
        """
        Test storage without target directory.
        """
        s = pote.PoteArchive(self.path + '-not-exists')
        self.assertJobs(s, [])

    def test_main(self):
        """
        Main test.
        """
        a = {'id': 'aaaaaaa',
             'time': 200}
        b = {'id': 'bbbbbbb',
             'time': 100}
        c = {'id': 'ccccccc',
             'time': 300}
        s = pote.PoteArchive(self.path)
        self.assertJobs(s, [])
        s.archive(a)
        self.assertJobs(s, [a])
        s.archive(b)
        self.assertJobs(s, [b, a])
        s.archive(c)
        self.assertJobs(s, [b, a, c])

    def assertJobs(self, storage, jobs):
        """
        Make assertion for current test list.

        :param storage: interface to the Archive.
        :type storage: pote.PoteArchive

        :param jobs: list of Job objects
        :type jobs: list of dicts
        """
        self.assertEqual(storage.dump(), jobs)
