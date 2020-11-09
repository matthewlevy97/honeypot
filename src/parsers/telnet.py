from core.bufferedsocket import BufferedSocket
import logging
import socket

logger = logging.getLogger(__name__)

class TelnetConnection(object):
    CODE_IAC             = 0xFF
    CODE_DONT            = 0xFE
    CODE_DO              = 0xFD
    CODE_WONT            = 0xFC
    CODE_WILL            = 0xFB
    CODE_SUB             = 0xFA
    CODE_GO_AHEAD        = 0xF9
    CODE_ERASE_LINE      = 0xF8
    CODE_ERASE_CHARACTER = 0xF7
    CODE_AYT             = 0xF6 # Are You There
    CODE_ABORT_OUTPUT    = 0xF5
    CODE_INTERRUPT_PROC  = 0xF4
    CODE_BREAK           = 0xF3
    CODE_DATA_MARK       = 0xF2
    CODE_NOP             = 0xF1
    CODE_SUB_END         = 0xF0
    def __init__(self, sock: socket.socket):
        self._buffered_sock = BufferedSocket(sock, timeout=1)
    def init(self) -> bool:
        code = self._buffered_sock.recv(1)
        while code and ord(code) == TelnetConnection.CODE_IAC:
            command = self._buffered_sock.recv(1)
            option = self._buffered_sock.recv(1)
            if not command or not option:
                logger.warning('No negotiation command received!')
                return False
            
            command = ord(command)
            option  = ord(option)
            if command == TelnetConnection.CODE_DO:
                self.send_command(TelnetConnection.CODE_DONT, option)
            elif command == TelnetConnection.CODE_DONT:
                self.send_command(TelnetConnection.CODE_WONT, option)
            elif command == TelnetConnection.CODE_WILL:
                self.send_command(TelnetConnection.CODE_WONT, option)
            elif command == TelnetConnection.CODE_WONT:
                self.send_command(TelnetConnection.CODE_DONT, option)
            elif command == TelnetConnection.CODE_SUB:
                logger.warning('Suboptions not supported')
                return False
            else:
                logger.warning('Unknown negotiation command: {}'.format(command))
                return False
            code = self._buffered_sock.recv(1)
        if code:
            self._buffered_sock.prepend_bytes(code)
        
        self._buffered_sock.set_timeout(10)
        return True
    def shutdown(self):
        # TODO
        return
    def send_command(self, command: bytes, *args: bytes) -> None:
        msg = bytes([TelnetConnection.CODE_IAC, command, *args])
        self._buffered_sock.send(msg)
    def send_data(self, data: bytes) -> None:
        self._buffered_sock.send(data)
    def recv_data(self) -> bytes:
        data = self._buffered_sock.recv_until(b'\x00')
        if data:
            data = data.strip()
        return data