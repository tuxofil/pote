"""
Interface to the persistent storage of finished tasks.
"""

import json
import logging
import os
import os.path
import shutil


class PoteArchive(object):
    """
    Interface to the persistent storage of finished tasks.
    """

    def __init__(self, path):
        """
        Constructor.

        :param path: path to an archive directory.
        :type path: string
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.path = os.path.abspath(path)
        self.logger.debug('started in %r', self.path)

    def archive(self, job, output_path=None):
        """
        Save job object to the storage.

        :param job: job details
        :type job: dict

        :param output_path: path to a file with test stdout and stderr
        :type output_path: NoneType or string
        """
        assert isinstance(job, dict)
        job_id = job['id']
        job_dir = self._job_dir(job_id)
        if not os.path.isdir(job_dir):
            os.makedirs(job_dir)
        if output_path is not None:
            job['log'] = 'stdout.log'
            shutil.copyfile(output_path, os.path.join(job_dir, job['log']))
        with open(os.path.join(job_dir, 'meta'), 'w') as fdescr:
            json.dump(job, fdescr)
        self.logger.debug('job %r archived to %r', job['id'], self.path)

    def dump(self):
        """
        Return a list of objects containing job data.

        :rtype: list of dicts
        """
        if not os.path.isdir(self.path):
            return []
        result = []
        for job_id in os.listdir(self.path):
            meta_path = os.path.join(self._job_dir(job_id), 'meta')
            with open(meta_path) as fdescr:
                result.append(json.load(fdescr))
        # sort them by creation time
        result.sort(key=lambda x: x['time'])
        return result

    def _job_dir(self, job_id):
        """
        Return path to a directory with archived job.

        :param job_id: job unique identifier
        :type job_id: string

        :rtype: string
        """
        return os.path.join(self.path, job_id)
