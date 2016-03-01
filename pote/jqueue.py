"""
Persistent storage for the job queue.
"""

import json
import logging
import os
import os.path


class PoteJobQueue(object):
    """
    Interface to the queue.
    """

    def __init__(self, path):
        """
        Constructor.

        :param path: path to a directory with queue data.
        :type path: string

        :param archive: link to an interface to Archive storage
        :type archive: pote.PoteArchive
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.path = os.path.abspath(path)
        self.logger.debug('started in %r', self.path)

    def save(self, job):
        """
        Save job object to the storage.

        :param job: job data
        :type job: dict
        """
        assert isinstance(job, dict)
        assert 'time' in job
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
        with open(self._job_path(job['id']), 'w') as fdescr:
            json.dump(job, fdescr)
        self.logger.debug('job %r enqueued to %r', job['id'], self.path)

    def get(self, job_id):
        """
        Fetch job data from the storage.

        :param job_id: job unique identifier
        :type job_id: string

        :rtype: dict
        """
        try:
            with open(self._job_path(job_id)) as fdescr:
                return json.load(fdescr)
        except IOError:
            # assume there is no such file
            pass

    def dump(self):
        """
        Return a list of objects containing job data.

        :rtype: list of dicts
        """
        if not os.path.isdir(self.path):
            return []
        jobs = [self.get(jid) for jid in os.listdir(self.path)]
        # sort them by creation time
        jobs.sort(key=lambda x: x['time'])
        return jobs

    def remove(self, job_id):
        """
        Drop job data from the Storage.

        :param job_id: job unique identifier
        :type job_id: string
        """
        os.unlink(self._job_path(job_id))

    def _job_path(self, job_id):
        """
        Return absolute path to a file with job data.

        :param job_id: job unique identifier
        :type job_id: string

        :rtype: string
        """
        return os.path.join(self.path, job_id)
