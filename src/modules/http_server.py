from core.honeybackend import backend_collector
from core.honeymodule import HoneyModule, HoneyHandler
from parsers.http import HTTPRequest, HTTPResponse
from config import config
import json
import logging
import socket

MODULE_NAME = 'HTTPModule'
logger = logging.getLogger(__name__)

class HTTPModule(HoneyModule):
    def __init__(self, address: str = '0.0.0.0', port: int = 8080):
        global MODULE_NAME
        super(HTTPModule, self).__init__(MODULE_NAME, HTTPHandler)
        self._address = address
        self._port    = port
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
        self.addThreatInfo('HTTP Method', request.method)
        self.addThreatInfo('HTTP Path', request.path)
        self.addThreatInfo('HTTP Content', request.content)
        self.addThreatInfo('HTTP Headers', json.dumps(request.headers))
        
        response = HTTPResponse(200)

        for param in request.params():
            for backend_name in config['modules'][MODULE_NAME]['backends']:
                backend = backend_collector.getBackend(backend_name)
                if not backend:
                    continue

                b = backend(self)
                b_response = b.handle_input(param[1].encode('utf-8'), one_shot=True)
                if b_response['success']:
                    self.addThreatInfo(b.get_name(), b.get_session_id())
                    if b_response['output']:
                        response.addContent(b_response['output'])

        s.send(response.build())
        s.close()