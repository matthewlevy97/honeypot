from core.bufferedsocket import BufferedSocket
import urllib.parse
import logging
import socket

logger = logging.getLogger(__name__)

class HTTPResponse(object):
    REASON_PHRASES = {
        200: 'OK',
        404: 'Not Found',
    }
    def __init__(self, status_code: int = 200, http_version: str = 'HTTP/1.1'):
        self.status_code  = status_code
        self.http_version = http_version
        self.headers = {}
        self.content = b''
    def setContent(self, content: bytes) -> None:
        self.content = content
    def addContent(self, content: bytes) -> None:
        if self.content:
            self.content += content
        else:
            self.content = content
    def addHeader(self, key: str, value: str) -> None:
        self.headers[key] = value
    def addHeaders(self, headers: tuple) -> None:
        for header in headers:
            self.addHeader(header[0], header[1])
    def build(self) -> bytes:
        ret = b''
        ret += '{} {} {}\r\n'.format(
            self.http_version, self.status_code,
            HTTPResponse.REASON_PHRASES[self.status_code]
        ).encode('utf-8')
        for header in self.headers:
            ret += '{}: {}\r\n'.format(header, self.headers[header]).encode('utf-8')
        if self.content:
            ret += 'Content-Length: {}\r\n'.format(len(self.content)).encode('utf-8')
        ret += b'\r\n'
        if self.content:
            ret += self.content
        return ret        

class HTTPRequest(object):
    def __init__(self, sock: socket.socket):
        self._buffered_sock = BufferedSocket(sock)
        self.method         = None
        self.path           = None
        self.http_version   = None
        self.headers        = {}
        self.content        = None
        self.parsed = self._parse_request()
    def _parse_request(self) -> bool:
        global logger
        start_line = self._buffered_sock.recv_until(b'\r\n').decode('utf-8')
        if not start_line:
            logger.error('No start line')
            return False
        
        start_line = list(filter(None, start_line.split(' ')))
        if len(start_line) != 3:
            logger.error('Invalid start line: {}'.format(start_line))
            return False
        self.method, self.path, self.http_version = start_line
        self.method = self.method.upper()

        line = self._buffered_sock.recv_until(b'\r\n').decode('utf-8')
        while line:
            header = line.split(':', 1)
            if len(header) != 2:
                logger.warning('Invalid header: {}'.format(line))
            else:
                self.headers[header[0].lower()] = header[1].strip()
            line = self._buffered_sock.recv_until(b'\r\n').decode('utf-8')
        
        if 'content-length' in self.headers:
            self.content = self._buffered_sock.recv(int(self.headers['content-length']))
        return True
    def params(self) -> list:
        if self.method == 'GET':
            params = self.path.split('?', 1)
            if len(params) != 2:
                return []
            return urllib.parse.parse_qsl(params[1])
        #TODO: Support POST methods
        return []