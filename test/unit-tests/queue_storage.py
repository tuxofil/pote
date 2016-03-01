"""
Unit test for the Job Queue Storage interface.
"""

import logging
import os
import os.path
import shutil
import time
import unittest

import pote.jqueue


logging.basicConfig(level=logging.DEBUG)


class PoteJobQueueTest(unittest.TestCase):
    """
    Unit test for the Job Queue Storage interface.
    """

    path = 'queue-storage.tmp'

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
        s = pote.jqueue.PoteJobQueue(self.path + '-not-exists')
        self.assertJobs(s, [])

    def test_main(self):
        """
        Main queue test.
        """
        a = {'id': 'aaaaaaa',
             'time': 200}
        b = {'id': 'bbbbbbb',
             'time': 100}
        c = {'id': 'ccccccc',
             'time': 300}
        s = pote.jqueue.PoteJobQueue(self.path)
        self.assertJobs(s, [])
        s.save(a)
        self.assertJobs(s, [a])
        self.assertEqual(s.get(a['id']), a)
        s.save(b)
        self.assertJobs(s, [b, a])
        self.assertEqual(s.get(b['id']), b)
        s.save(c)
        self.assertJobs(s, [b, a, c])
        self.assertEqual(s.get(c['id']), c)
        s.remove(a['id'])
        self.assertJobs(s, [b, c])
        self.assertIsNone(s.get(a['id']))
        s.remove(b['id'])
        self.assertJobs(s, [c])
        self.assertIsNone(s.get(b['id']))
        s.remove(c['id'])
        self.assertJobs(s, [])
        self.assertIsNone(s.get(c['id']))

    def assertJobs(self, storage, jobs):
        """
        Make assertion for current test list.

        :param storage: interface to the queue.
        :type storage: pote.PoteJobQueue

        :param jobs: list of Job objects
        :type jobs: list of dicts
        """
        self.assertEqual(storage.dump(), jobs)
