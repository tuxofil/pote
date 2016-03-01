"""
Main unit test.
"""

import httplib
import json
import os.path
import shutil
import subprocess
import time
import unittest

from pote.scheduler import (STATUS_ENQUEUED, STATUS_STARTING,
                            STATUS_RUNNING, STATUS_FAILED,
                            STATUS_DONE)

class PoteMainTest(unittest.TestCase):
    """
    Main unit test for Python Online Test Executor.
    """

    def setUp(self):
        """
        Test prepare recipes.
        """
        self.log = open('poted.log', 'w')
        if os.path.isdir('poted'):
            shutil.rmtree('poted')
        self.proc = subprocess.Popen(
            ['../../bin/poted', '--verbose',
             '--envos-path', 'poted/envos',
             '--tests-path', '../../tests',
             '--queue-path', 'poted/tests',
             '--archive-path', 'poted/archive'],
            stdout=self.log, stderr=self.log,
            env={'PYTHONPATH': '../../'}, close_fds=True)
        # wait until server starts
        time.sleep(2)

    def tearDown(self):
        """
        Test destroy recipes.
        """
        self.proc.kill()
        self.proc.wait()
        self.log.close()

    def test_fast_tests(self):
        """
        Lightning fast tests.
        """
        self.assertEmpty('/job')
        self.assertEmpty('/archive')
        j1_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'fast_good'})
        time.sleep(1)
        self.assertEmpty('/job')
        self.assertIn('/archive', j1_id, STATUS_DONE)
        j2_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'fast_bad'})
        time.sleep(1)
        self.assertEmpty('/job')
        self.assertIn('/archive', j2_id, STATUS_FAILED)

    def test_normal_tests(self):
        """
        Normal duration tests.
        """
        self.assertEmpty('/job')
        self.assertEmpty('/archive')
        j1_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'normal_good'})
        time.sleep(1)
        self.assertIn('/job', j1_id, STATUS_RUNNING)
        time.sleep(5)
        self.assertEmpty('/job')
        self.assertIn('/archive', j1_id, STATUS_DONE)
        j2_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'normal_bad'})
        time.sleep(1)
        self.assertIn('/job', j2_id, STATUS_RUNNING)
        time.sleep(5)
        self.assertEmpty('/job')
        self.assertIn('/archive', j2_id, STATUS_FAILED)

    def test_queue(self):
        """
        Queueing jobs into one environment.
        """
        self.assertEmpty('/job')
        self.assertEmpty('/archive')
        j1_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'normal_good'})
        j2_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'normal_bad'})
        time.sleep(1)
        self.assertIn('/job', j1_id, STATUS_RUNNING)
        self.assertIn('/job', j2_id, STATUS_ENQUEUED)
        time.sleep(5)
        self.assertNotIn('/job', j1_id)
        self.assertIn('/job', j2_id, STATUS_RUNNING)
        time.sleep(6)
        self.assertEmpty('/job')
        self.assertIn('/archive', j1_id, STATUS_DONE)
        self.assertIn('/archive', j2_id, STATUS_FAILED)

    def test_run_in_parallel_envos(self):
        """
        Queueing jobs into different environments
        so they can be executed in parallel.
        """
        self.assertEmpty('/job')
        self.assertEmpty('/archive')
        j1_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 0,
                                           'test': 'normal_good'})
        j2_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 1,
                                           'test': 'normal_good'})
        j3_id = self._req('POST', '/job', {'user': 'u',
                                           'envo': 2,
                                           'test': 'normal_good'})
        time.sleep(1)
        self.assertIn('/job', j1_id, STATUS_RUNNING)
        self.assertIn('/job', j2_id, STATUS_RUNNING)
        self.assertIn('/job', j3_id, STATUS_RUNNING)
        time.sleep(5)
        self.assertEmpty('/job')
        self.assertIn('/archive', j1_id, STATUS_DONE)
        self.assertIn('/archive', j2_id, STATUS_DONE)
        self.assertIn('/archive', j3_id, STATUS_DONE)

    def assertEmpty(self, url):
        """
        Assert job list is empty.

        :param url: URL from which to fetch job list.
        :type url: string
        """
        self.assertEqual(self._req('GET', url), [])

    def assertIn(self, url, job_id, status=None):
        """
        Check job list for a job with given ID.

        :param url: URL from which to fetch job list.
        :type url: string

        :param job_id: job unique identifier
        :type job_id: string

        :param status: expected status of the searched job
        :type status: string or NoneType
        """
        jobs = self._req('GET', url)
        found = False
        for job in jobs:
            if job['id'] == job_id:
                found = True;
                if status is not None:
                    self.assertEqual(job['status'], status)
                break
        self.assertTrue(found)

    def assertNotIn(self, url, job_id):
        """
        Check job list to not contain a job with given ID.

        :param url: URL from which to fetch job list.
        :type url: string

        :param job_id: job unique identifier
        :type job_id: string
        """
        jobs = self._req('GET', url)
        found = False
        for job in jobs:
            if job['id'] == job_id:
                found = True;
                break
        self.assertFalse(found)

    def _req(self, method, url, body=None):
        """
        Make HTTP request to the RESTful Pote server.
        Return response entity, decoded from JSON.

        :param method: HTTP method to use
        :type method: 'GET' or 'POST'

        :param url: URL
        :type url: string

        :param body: request entity (will be encoded as JSON)
        :type body: any or NoneType

        :rtype: any
        """
        headers = {}
        if body is not None:
            body = json.dumps(body)
            headers = {'content-type': 'application/json'}
        connection = httplib.HTTPConnection('127.1', 8901)
        connection.request(method, url, body, headers)
        reply = connection.getresponse()
        entity = None
        if 200 <= reply.status < 300 and reply.status != 204:
            entity = json.loads(reply.read())
        connection.close()
        return entity
