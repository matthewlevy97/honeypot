import socket
import logging

logger = logging.getLogger(__name__)

class BufferedSocket(object):
    MAX_BUFFER_SIZE     = (1024 * 64)
    SOCKET_TIMEOUT_SECS = 5
    def __init__(self, sock: socket.socket, buffer_size: int = 256, timeout: int = SOCKET_TIMEOUT_SECS):
        self._socket      = sock
        self._buffer_size = buffer_size
        self._buffer      = b''
        sock.settimeout(timeout)
    def set_timeout(self, timeout: int):
        self._socket.settimeout(timeout)
    def send(self, data: bytes, flags: int = 0) -> int:
        global logger
        ret = -1
        try:
            ret = self._socket.send(data)
        except Exception as e:
            logger.debug('Error on send: {}'.format(e))
        return ret
    
    def recv(self, num_bytes: int = 256, flags: int = 0) -> bytes:
        global logger
        if num_bytes > BufferedSocket.MAX_BUFFER_SIZE:
            num_bytes = BufferedSocket.MAX_BUFFER_SIZE
        
        if len(self._buffer) < num_bytes:
            try:
                self._buffer += self._socket.recv(num_bytes)
            except Exception as e:
                logger.debug('Error on recv: {}'.format(e))
        
        ret = self._buffer[:num_bytes]
        self._buffer = self._buffer[num_bytes:]
        return ret
    
    def recv_until(self, key: bytes, max_bytes: int = 65536) -> bytes:
        global logger
        ret = b''

        if max_bytes > BufferedSocket.MAX_BUFFER_SIZE:
            max_bytes = BufferedSocket.MAX_BUFFER_SIZE

        pos = self._buffer.find(key)
        old_len = len(self._buffer)
        while pos < 0 and old_len < max_bytes:
            try:
                data = self._socket.recv(self._buffer_size)
            except Exception as e:
                logger.debug('Error on recv: {}'.format(e))
                break
            if len(data) <= 0:
                break

            self._buffer += data
            pos = self._buffer.find(key)
            old_len = len(self._buffer)
        
        if pos >= 0:
            ret = self._buffer[:pos]
            self._buffer = self._buffer[pos+len(key):]
        return ret

    def prepend_bytes(self, data: bytes) -> None:
        self._buffer = data + self._buffer
    
    def close(self) -> None:
        self._socket.close()
    
    def get_socket(self) -> socket.socket:
        return self._socket