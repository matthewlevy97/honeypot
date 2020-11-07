import socket

class BufferedSocket(object):
    MAX_BUFFER_SIZE = (1024 * 64)
    def __init__(self, sock: socket.socket, buffer_size: int = 256):
        self._socket      = sock
        self._buffer_size = buffer_size
        self._buffer      = b''
    
    def send(self, data: bytes, flags: int = 0) -> int:
        return self._socket.send(data, flags)
    
    def recv(self, num_bytes: int = 256, flags: int = 0) -> bytes:
        if num_bytes > BufferedSocket.MAX_BUFFER_SIZE:
            num_bytes = BufferedSocket.MAX_BUFFER_SIZE
        
        if len(self._buffer) < num_bytes:
            self._buffer += self._socket.recv(num_bytes)
        
        ret = self._buffer[:num_bytes]
        self._buffer = self._buffer[num_bytes:]
        return ret
    
    def recv_until(self, key: bytes, max_bytes: int = 65536) -> bytes:
        ret = None

        if max_bytes > BufferedSocket.MAX_BUFFER_SIZE:
            max_bytes = BufferedSocket.MAX_BUFFER_SIZE

        pos = self._buffer.find(key)
        old_len = len(self._buffer)
        while pos < 0 and old_len < max_bytes:
            try:
                data = self._socket.recv(self._buffer_size)
            except:
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
    
    def close(self) -> None:
        self._socket.close()
    
    def get_socket(self) -> socket.socket:
        return self._socket