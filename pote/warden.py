"""
Thread which starts target test, waits for the test to finish
and collects results.
"""

import logging
import os
import os.path
import Queue
import shutil
import subprocess
import threading
import time


class PoteWarden(threading.Thread):
    """
    Test Job Warden thread.
    """

    def __init__(self, scheduler, tests, path, envo):
        """
        Constructor.

        :param scheduler: interface to the Scheduler thread.
        :type scheduler: pote.PoteScheduler

        :param tests: interface to the Tests Storage.
        :type tests: pote.PoteTests

        :param path: base path of the environment.
        :type path: string

        :param envo: envo ID. Passed only for logging.
        :type envo: integer
        """
        threading.Thread.__init__(self)
        self.logger_id = '%s#%r' % (self.__class__.__name__, envo)
        self.logger = logging.getLogger(self.logger_id)
        self.scheduler = scheduler
        self.tests = tests
        self.path = os.path.abspath(path)
        self.queue = Queue.Queue(maxsize=1)
        self.logger.debug('started at %r', self.path)
        self.busy = threading.Lock()

    @classmethod
    def running(cls, *args, **kwargs):
        """
        Create and start a new warden instance.
        Return a link to the object created.
        See constructor description for further details
        about arguments.

        :rtype: pote.PoteWarden
        """
        instance = cls(*args, **kwargs)
        instance.start()
        return instance

    def execute(self, job):
        """
        Give a job to the warden.

        :param job: job data object
        :type job: dict

        :rtype: boolean
        """
        if not self.isAlive():
            raise RuntimeError('%r is dead', self.logger_id)
        if self.busy.acquire(False):
            try:
                self.queue.put_nowait(job)
                return True
            except Queue.Full:
                pass
        return False

    def run(self):
        """
        Main thread activity.
        """
        while True:
            job = self.queue.get()
            self.logger.info('got new job: %r', job)
            try:
                self._process(job)
            except Exception as exc:
                self.logger.error(
                    'job %r crashed', job['id'], exc_info=True)
                self.scheduler.notify_job_failed(
                    job['id'], 'crashed: %r' % exc)
                self.scheduler.notify_job_result(job['id'])
            self.queue.task_done()
            self.busy.release()

    def _process(self, job):
        """
        Execute the test job.

        :param job: job data object
        :type job: dict
        """
        # Prepare working directory
        if not self._clean():
            self.scheduler.notify_job_failed(
                job['id'], 'working dir not ready')
            self.scheduler.notify_job_result(job['id'])
            return
        # construct environment and spawn a process
        environ = dict(os.environ)
        environ.update(
            {'LC_ALL': 'C',
             'HOME': self.path,
             'PYTHONPATH': self.tests.path})
        output_path = os.path.join(self.path, 'stdout.txt')
        with open(output_path, 'wb') as fdescr:
            try:
                proc = subprocess.Popen(
                    ['python', '-m', job['test']],
                    stdout=fdescr, stderr=fdescr,
                    env=environ, close_fds=True)
                self.logger.info('job %r started', job['id'])
            except OSError as exc:
                self.logger.debug(
                    'test spawn failed for %r', job['id'], exc_info=True)
                self.scheduler.notify_job_failed(job['id'], exc.message)
                self.scheduler.notify_job_result(job['id'])
                return
            self.scheduler.notify_job_started(job['id'])
            # wait for the process to finish
            deadline = time.time() + job['max_duration']
            while proc.poll() is None and time.time() < deadline:
                time.sleep(0.5)
            if time.time() > deadline:
                proc.kill()
                proc.wait()
                self.logger.debug('test timeouted: %r', job['id'])
                self.scheduler.notify_job_stopped(job['id'])
                self.scheduler.notify_job_failed(job['id'], 'timeouted')
            else:
                proc.wait()
                self.scheduler.notify_job_stopped(job['id'])
                if proc.returncode == 0:
                    self.logger.info('job %r done', job['id'])
                    self.scheduler.notify_job_done(job['id'])
                else:
                    self.logger.error(
                        'job %r failed with exitcode %r',
                        job['id'], proc.returncode)
                    self.scheduler.notify_job_failed(
                        job['id'], 'exit code %r' % proc.returncode)
        # collect test results
        self.scheduler.notify_job_result(job['id'], output_path)

    def _clean(self):
        """
        Create the working directory if not exists,
        remove any files from the directory.
        Return True oif working directory is ready,
        and False otherwise.

        :rtype: boolean
        """
        try:
            if os.path.isfile(self.path):
                os.unlink(self.path)
            if os.path.isdir(self.path):
                shutil.rmtree(self.path)
            os.makedirs(self.path)
            return True
        except OSError:
            self.logger.error(
                'failed to prepare working directory %r',
                self.path, exc_info=True)
            return False
