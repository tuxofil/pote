"""
RestFul API Server.
"""

import BaseHTTPServer
import cgi
import json
import logging
import SocketServer
import urlparse
import uuid


class RepliedException(Exception):
    """
    Raised when HTTP request processing is finished and
    there is nothing to do more.
    """
    pass


class PoteApiServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """
    RestFul API Server.
    """

    def __init__(self, bindaddr, bindport, scheduler, tests, archive):
        """
        Pote RestFul API Server constructor.

        :param bindaddr: IP address to listen to
        :type bindaddr: string

        :param bindport: TCP port number to listen to
        :type bindport: integer

        :param scheduler: link to a Scheduler activity.
        :type scheduler: pote.scheduler.Scheduler

        :param tests: link to a TestSet storage.
        :type tests: pote.tests.PoteTests

        :param archive: interface to the Archive Storage
        :type archive: pote.PoteArchive
        """
        self.bindaddr = bindaddr
        self.bindport = bindport
        self.scheduler = scheduler
        self.tests = tests
        self.archive = archive
        self.logger = logging.getLogger(self.__class__.__name__)
        BaseHTTPServer.HTTPServer.__init__(
            self, (bindaddr, bindport), PoteApiServerHandler)


class PoteApiServerHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    HTTP Request Handler.
    """

    def __getattr__(self, attr):
        """
        Standard method override.
        Redirects invocation of methods like do_GET, do_POST, etc.
        to the 'process()' method.
        """
        if attr.startswith('do_'):
            return self.process
        raise AttributeError('%r has no member like %r', self, attr)

    def process(self):
        """
        Wrapper for the process_unsafe() method which catches all
        raised exceptions and logs them.
        The method is vital because standard implementation of
        BaseHTTPServer.BaseHTTPRequestHandler silently drops all
        exceptions raised during HTTP request processing.
        """
        try:
            try:
                self.process_unsafe()
            except RepliedException:
                pass
            except NotImplementedError:
                self.logger.error('Not implemented', exc_info=True)
                self.send_error(501)
            except Exception:
                self.logger.error('Crashed', exc_info=True)
                self.send_error(500)
        except RepliedException:
            # catch exceptions raised from overrided send_error()
            pass

    def process_unsafe(self):
        """
        HTTP request processing entry point.
        """
        if self.command not in ('GET', 'POST'):
            self.send_response(405)
            self.send_header('Allow', 'GET, POST')
            self.send_header('Content-Type', 'text/plain')
            message = '%s\n' % self.responses[405][1]
            self.send_header('Content-Length', len(message))
            self.end_headers()
            self.wfile.write(message)
            return
        parsed = urlparse.urlparse(self.path)
        # URI router
        path = parsed.path.strip('/')
        if self.command == 'GET':
            if path == 'ping':
                self.send_response(204)
                self.end_headers()
                raise RepliedException
            elif path == 'envo':
                self.reply_with_json(self.server.scheduler.envos_count)
            elif path == 'test':
                self.reply_with_json(sorted(self.server.tests.available()))
            elif path == 'job':
                self.reply_with_json(self.server.scheduler.queued())
            elif path == 'archive':
                self.reply_with_json(self.server.archive.dump())
        if self.command == 'POST':
            if path == 'job':
                request = self._read_and_decode_entity()
                self.logger.debug('new job request: %r', request)
                if not isinstance(request, dict):
                    self.send_error(400, 'Bad request object')
                # check incoming values
                user = request.get('user')
                if not (isinstance(user, basestring) and len(user)):
                    self.send_error(400, 'Bad user name')
                try:
                    envo = int(request.get('envo'))
                    if not (0 <= envo <= self.server.scheduler.envos_count):
                        self.send_error(400, 'Bad environment ID')
                except ValueError:
                    self.send_error(400, 'Bad environment ID')
                test = request.get('test')
                if test not in self.server.tests:
                    self.send_error(400, 'Bad test set name')
                job_id = uuid.uuid4().hex
                self.server.scheduler.notify_job_add(
                    {'id': job_id,
                     'user': user,
                     'envo': envo,
                     'test': test,
                     'max_duration': 90})
                self.reply_with_json(job_id, 201)
        self.send_error(404)

    def reply_with_json(self, obj, status_code=200):
        """
        Reply to the client with JSON object.

        :param obj: object to send
        :type obj: any

        :param status_code: HTTP status code to reply
        :type status_code: integer
        """
        encoded = json.dumps(obj)
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(encoded))
        self.end_headers()
        self.wfile.write(encoded)
        raise RepliedException

    def _read_and_decode_entity(self):
        """
        Read and decode JSON object from the request. Return the decoded
        object itself on success or sends an error response to the
        client in case of error.
        FIXME: supports only HTTP/1.0: no Transfer-Encoding and
           Transfer-Length will be processed.

        :rtype: any
        """
        try:
            content_length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            self.send_error(400, 'Bad Content-Length')
        if content_length == 0:
            return None
        content_type = self.headers.get('Content-Type')
        if content_type is None:
            self.send_error(415, 'Content-Type not defined')
        ct_main, _ct_fields = cgi.parse_header(content_type)
        if ct_main.lower() != 'application/json':
            self.send_error(
                415, 'Unsupported Content-Type. Use application/json')
        encoded_entity = self.rfile.read(content_length)
        if len(encoded_entity) > content_length:
            encoded_entity = encoded_entity[:content_length]
            self.logger.warning('extra bytes found')
        elif len(encoded_entity) < content_length:
            msg = 'only %r bytes received but %r expected' % \
                (len(encoded_entity), content_length)
            self.send_error(400, msg)
        try:
            return json.loads(encoded_entity)
        except ValueError:
            self.send_error(400, 'Bad JSON')

    @property
    def logger(self):
        """
        Return a link to the logger.

        :rtype: logging.Logger
        """
        real_addr = self.headers.get('x-real-ip')
        real_port = self.headers.get('x-real-port')
        if real_addr and real_port:
            return logging.getLogger('{0}:{1}'.format(real_addr, real_port))
        return logging.getLogger('{0}:{1}'.format(*self.client_address))

    def log_message(self, msg_format, *args):
        """
        Override the BaseHTTPServer.BaseHTTPRequestHandler.log_message().
        There is no stdout in daemonized state so relay messages
        to the 'logging' facility.
        """
        self.logger.debug(msg_format, *args)

    def version_string(self):
        """
        Override the BaseHTTPServer.BaseHTTPRequestHandler.version_string().
        Hide the version of BaseHTTPServer and Python version in
        the 'Server' HTTP header and replace them with custom value.

        :rtype: string
        """
        return "Pote/0.1"

    def send_error(self, *args, **kwargs):
        """
        Override for BaseHTTPServer.BaseHTTPRequestHandler.send_error().
        """
        BaseHTTPServer.BaseHTTPRequestHandler.send_error(self, *args, **kwargs)
        raise RepliedException
