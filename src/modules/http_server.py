from core.honeybackend import backend_collector
from core.honeymodule import HoneyModule, HoneyHandler
from parsers.http import HTTPRequest, HTTPResponse
from config import config
import json
import logging
import socket
import time

MODULE_NAME = 'HTTPModule'
logger = logging.getLogger(__name__)

class HTTPModule(HoneyModule):
    def __init__(self, address: str = None, port: int = 0):
        global MODULE_NAME
        super(HTTPModule, self).__init__(MODULE_NAME, HTTPHandler)
        if address:
            self._address = address
        else:
            self._address = config['modules'][MODULE_NAME]['default']['address']
        if port > 0:
            self._port = port
        else:
            self._port = config['modules'][MODULE_NAME]['default']['port']
        self._server  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def bind_server(self) -> bool:
        self._server.bind((self._address, self._port))
        self._server.listen(2)
    def get_server(self) -> socket.socket:
        return self._server

class HTTPHandler(HoneyHandler):
    def __init__(self, module: HoneyModule, server: socket.socket):
        super(HTTPHandler, self).__init__(module, server)
    def run(self) -> None:
        global logger

        s, addr = self.server.accept()
        self.createThreatFromSocket(s)
        
        request = HTTPRequest(s)
        self.addThreatInfo('REQUEST_METHOD', request.method)
        self.addThreatInfo('REQUEST_PATH', request.path)
        self.addThreatInfo('REQUEST_CONTENT', request.content)
        self.addThreatInfo('REQUEST_HEADERS', json.dumps(request.headers))
        
        response = HTTPResponse(200)
        response.addHeader('date', time.strftime('%a, %d %b %Y %H:%M:%S %Z', time.gmtime()))
        response.addHeader('server', config['modules'][MODULE_NAME]['advertise_version'])

        for backend_name in config['modules'][MODULE_NAME]['path_backends']:
            backend = backend_collector.getBackend(backend_name)
            if not backend:
                logger.warning('Cannot find backend: {}'.format(backend_name))
                continue
            b = backend(self)
            b_response = b.handle_input(request.path.encode('utf-8'), one_shot=True)
            if b_response['success']:
                self.addThreatInfo('BACKEND_SESSIONID', b.get_session_id())
                if b_response['output']:
                    response.addContent(b_response['output'])

        for param in request.params():
            for backend_name in config['modules'][MODULE_NAME]['param_backends']:
                backend = backend_collector.getBackend(backend_name)
                if not backend:
                    continue
                b = backend(self)
                b_response = b.handle_input(param[1].encode('utf-8'), one_shot=True)
                if b_response['success']:
                    self.addThreatInfo('BACKEND_SESSIONID', b.get_session_id())
                    if b_response['output']:
                        response.addContent(b_response['output'])

        s.send(response.build())
        s.close()