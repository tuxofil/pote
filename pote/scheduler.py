"""
Test tasks scheduler thread.
"""

import logging
import os.path
import Queue
import threading
import time

from .jqueue import PoteJobQueue
from .warden import PoteWarden


# job statuses
STATUS_ENQUEUED = 'enqueued'
STATUS_STARTING = 'starting'
STATUS_RUNNING = 'running'
STATUS_DONE = 'done'
STATUS_FAILED = 'failed'

# event types
EVENT_ADD = 'add'
EVENT_FAILED = 'failed'
EVENT_STARTED = 'started'
EVENT_STOPPED = 'stopped'
EVENT_SUCCESS = 'success'
EVENT_RESULT = 'result'

KNOWN_EVENTS = [EVENT_ADD,
                EVENT_FAILED,
                EVENT_STARTED,
                EVENT_STOPPED,
                EVENT_SUCCESS,
                EVENT_RESULT]


class PoteScheduler(threading.Thread):
    """
    Test tasks scheduler.
    """

    def __init__(self, envos_count, envos_path, queue_path, tests, archive):
        """
        Constructor.

        :param envos_count: how many environments to use.
        :type envos_count: integer

        :param envos_path: base path for work directories of environments
        :type envos_path: string

        :param queue_path: path of a directory for persistent job queues
        :type queue_path: string

        :param tests: interface to the available tests storage.
        :type tests: pote.PoteTests

        :param archive: interface to the Archive Storage
        :type archive: pote.PoteArchive
        """
        threading.Thread.__init__(self)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.daemon = True
        self.jobs = None
        self.queues = None
        self.wardens = None
        self.envos_count = envos_count
        self.envos_path = envos_path
        self.tests = tests
        self.queue_path = queue_path
        self.archive = archive
        self.mailbox = Queue.Queue()

    def envos(self):
        """
        Return list of available environment IDs.

        :rtype: list of integers
        """
        return range(self.envos_count)

    def queued(self):
        """
        Return list of all jobs queued.

        :rtype: list of dicts
        """
        jobs = [job for queue in self.queues for job in queue.dump()]
        jobs.sort(key=lambda x: x['time'])
        return jobs

    def notify_job_add(self, job):
        """
        Tell the Scheduler to enqueue a new job.

        :param job: new job data.
        :type job: dict
        """
        self._notify(EVENT_ADD, job)

    def notify_job_started(self, job_id):
        """
        Tell the Scheduler the job just started for execution.

        :param job_id: job identifier.
        :type job_id: string
        """
        self._notify(EVENT_STARTED, job_id)

    def notify_job_stopped(self, job_id):
        """
        Tell the Scheduler the job is finished.

        :param job_id: job identifier.
        :type job_id: string
        """
        self._notify(EVENT_STOPPED, job_id)

    def notify_job_done(self, job_id):
        """
        Tell the Scheduler the job is succeeded.

        :param job_id: job identifier.
        :type job_id: string
        """
        self._notify(EVENT_SUCCESS, job_id)

    def notify_job_failed(self, job_id, reason=None):
        """
        Tell the Scheduler the job execution is failed.

        :param job_id: job identifier.
        :type job_id: string

        :param reason: failure reason.
        :type reason: string
        """
        self._notify(EVENT_FAILED, (job_id, reason))

    def notify_job_result(self, job_id, data=None):
        """
        Send job results to the Scheduler.

        :param job_id: job identifier.
        :type job_id: string

        :param data: job execution results
        :type data: any
        """
        self._notify(EVENT_RESULT, (job_id, data))

    # ----------------------------------------------------------------------
    # end of public API

    def run(self):
        """
        Thread main activity.
        """
        # Initialize persistent job queues
        self.queues = \
            [PoteJobQueue(os.path.join(self.queue_path, str(envo_id)))
             for envo_id in range(self.envos_count)]
        # Start wardens
        self.wardens = \
            [self._start_warden(envo_id)
             for envo_id in range(self.envos_count)]
        # Read persistent queue for old jobs
        self.jobs = {job['id']: job for job in self.queued()}
        for job_id in self.jobs:
            if self.jobs[job_id]['status'] != STATUS_ENQUEUED:
                # reset job state
                self.jobs[job_id]['status'] = STATUS_ENQUEUED
                self._update_job(self.jobs[job_id])
            self._send_to_warden(self.jobs[job_id])
        # Main loop
        while True:
            event = self.mailbox.get()
            self.logger.debug('got new event: %r', event)
            try:
                assert isinstance(event, dict)
                assert event['type'] in KNOWN_EVENTS
                self._handle_event(event['type'], event['time'], event['data'])
                self.logger.debug('event %r processed', event)
            except Exception:
                self.logger.error(
                    'event processing crashed. Event was: %r', event,
                    exc_info=True)
            self.mailbox.task_done()

    def _start_warden(self, envo_id):
        """
        Launch wrden thread for environment.

        :param envo_id: environment unique identifier
        :type envo_id: integer

        :rtype: pote.PoteWarden
        """
        return PoteWarden.running(
            self, self.tests,
            os.path.join(self.envos_path, str(envo_id)),
            envo_id)

    def _notify(self, event_type, data=None):
        """
        Send event to the Scheduler.

        :param event_type: event type to send
        :type event_type: string

        :param data: event details
        :type data: any
        """
        assert self.isAlive()
        self.mailbox.put(
            {'type': event_type,
             'time': time.time(),
             'data': data})

    def _handle_event(self, event_type, event_time, data):
        """
        Process incoming event.

        :param event_type: event type identifier
        :type event_type: string, one of KNOWN_EVENTS

        :param event_time: event timestamp (seconds till Unix Epoch)
        :type event_time: number

        :param data: event details
        :type data: any
        """
        if event_type == EVENT_ADD:
            job = data
            job['time'] = event_time
            job['status'] = STATUS_ENQUEUED
            self._update_job(job)
            self.jobs[job['id']] = data
            self.logger.info('job enqueued: %r', job)
            self._send_to_warden(job)
        elif event_type == EVENT_STARTED:
            job_id = data
            job = self.jobs[job_id]
            job['started'] = event_time
            job['status'] = STATUS_RUNNING
            self._update_job(job)
            self.logger.info('job started: %r', job_id)
        elif event_type == EVENT_STOPPED:
            job_id = data
            job = self.jobs[job_id]
            job['stopped'] = time.time()
            self._update_job(job)
            self.logger.debug('job stopped: %r', job_id)
        elif event_type == EVENT_SUCCESS:
            job_id = data
            job = self.jobs[job_id]
            job['status'] = STATUS_DONE
            self._update_job(job)
            self.logger.info('job succeeded: %r', job_id)
        elif event_type == EVENT_FAILED:
            (job_id, reason) = data
            job = self.jobs[job_id]
            job['status'] = STATUS_FAILED
            job['reason'] = reason
            self.logger.info('job %r failed: %r', job_id, reason)
        elif event_type == EVENT_RESULT:
            (job_id, output_path) = data
            job = self.jobs[job_id]
            self._archive_job(job, output_path)
            # search pending job for this envo
            envo = job['envo']
            pending_job = None
            for job in self.queues[envo].dump():
                if job['status'] == STATUS_ENQUEUED:
                    pending_job = job
                    break
            if pending_job is not None:
                self._send_to_warden(pending_job)

    def _update_job(self, job):
        """
        Save updated job to the persistent queue.

        :param job: job details
        :type job: dict
        """
        self.queues[job['envo']].save(job)

    def _send_to_warden(self, job):
        """
        Try to send job to a warden process for execution.

        :param job: job details
        :type job: dict

        :rtype: boolean
        """
        envo = job['envo']
        is_sent = self.wardens[envo].execute(job)
        if is_sent:
            self.logger.info('job sent for execution: %r', job['id'])
            job['status'] = STATUS_STARTING
            self._update_job(job)
        else:
            self.logger.debug(
                'execution queue for envo #%r is full.'
                ' Job %r still pending', envo, job['id'])
        return is_sent

    def _archive_job(self, job, output_path):
        """
        Move job to the Archive.

        :param job: job details
        :type job: dict

        :param output_path: path to a file with test output.
        :type output_path: string or NoneType
        """
        job_id = job['id']
        self.archive.archive(job, output_path)
        self.queues[job['envo']].remove(job_id)
        del self.jobs[job_id]
        self.logger.info('job archived: %r', job)
