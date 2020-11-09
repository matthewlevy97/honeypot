from core.honeybackend import backend_collector
from core.honeymodule import HoneyModule, HoneyHandler
from config import config
from parsers.telnet import TelnetConnection
import logging
import socket

MODULE_NAME = 'TelnetModule'
logger      = logging.getLogger(__name__)

class TelnetModule(HoneyModule):
    def __init__(self, address: str = None, port: int = 0):
        global MODULE_NAME
        super(TelnetModule, self).__init__(MODULE_NAME, TelnetHandler)
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

class TelnetHandler(HoneyHandler):
    def __init__(self, module: HoneyModule, server: socket.socket):
        super(TelnetHandler, self).__init__(module, server)
    def run(self) -> None:
        global logger

        s, addr = self.server.accept()
        self.createThreatFromSocket(s)

        telnet_connection = TelnetConnection(s)
        if telnet_connection.init():
            self._handle_connection(telnet_connection)

        telnet_connection.shutdown()
        s.close()
    def _handle_connection(self, telnet_connection: TelnetConnection) -> None:
        global logger
        telnet_connection.send_data(config['modules'][MODULE_NAME]['advertise_version'].encode('utf-8'))
        if not self._do_login(telnet_connection):
            logger.info('Login Failed')
            return
        
        shell = backend_collector.getBackend(config['modules'][MODULE_NAME]['shell_backend'])(self)
        if not shell:
            logger.warning('Cannot find backend: {}'.format(config['modules'][MODULE_NAME]['shell_backend']))
            return
        while True:
            telnet_connection.send_data(shell.get_prompt().encode('utf-8'))
            command = telnet_connection.recv_data()
            if not command:
                continue

            self.addThreatInfo('COMMAND', command)
            shell_response = shell.handle_input(b'\r\n' + command + b'\r\n')
            telnet_connection.send_data(shell_response['output'])
            if shell_response['exit']:
                break

        return
    def _do_login(self, telnet_connection: TelnetConnection) -> bool:
        usernames = config['modules'][MODULE_NAME]['auth']['usernames']
        passwords = config['modules'][MODULE_NAME]['auth']['passwords']
        for attempts in range(config['modules'][MODULE_NAME]['auth']['attempts']):
            telnet_connection.send_data(b'\r\nlogin: ')
            username = telnet_connection.recv_data()
            if not username:
                return False
            telnet_connection.send_data(b'\r\npassword: ')
            password = telnet_connection.recv_data()
            if not password:
                return False
            
            if username.decode('utf-8') in usernames and password.decode('utf-8') in passwords:
                return True
            elif attempts != config['modules'][MODULE_NAME]['auth']['attempts'] - 1:
                telnet_connection.send_data(b'\r\nLogin incorrect')
        if config['modules'][MODULE_NAME]['auth']['allow_after_fail']:
            return True
        telnet_connection.send_data(b'\r\nLogin incorrect')
        return False