from backends._busybox.busybox_command import BusyBoxCommand
from backends._busybox.wget import BusyBoxWget
from backends._busybox.echo import BusyBoxEcho
from core.honeybackend import HoneyBackend
from core.honeymodule import HoneyHandler
from config import config
import logging
import json

# TODO: Switch to gnu_getopt() ???

BACKEND_NAME = 'BusyBox'
logger = logging.getLogger(__name__)

class BusyBox(HoneyBackend):
    COMMANDS = {
        'echo': BusyBoxEcho,
        'wget': BusyBoxWget
    }
    def __init__(self, handler: HoneyHandler):
        super(BusyBox, self).__init__(BACKEND_NAME, handler)
        self._buffer = b''
        self._previous_return_value = 0
    def handle_input(self, data: bytes, one_shot: bool = False) -> dict:
        self._buffer += data
        
        statement = self._getStatement(one_shot)
        ret_val = 1
        output, actions, ret_val = self._parse_statement(statement.decode('utf-8'))
        for action in actions:
            if type(action['data']) == str:
                self.addBackendAction(action['action'], action['data'])
            else:
                self.addBackendAction(action['action'], json.dumps(action['data']))

        self._previous_return_value = ret_val
        return {
            'success': statement != None,
            'output': output.encode('utf-8') if output else None
        }
    def help(self) -> str:
        ret = ''
        for command in BusyBox.COMMANDS:
            ret += '{}, '.format(command)
        if ret:
            return ret[:-2]
        return ret
        
    def _getStatement(self, one_shot: bool):
        pos_newline   = self._buffer.find(b'\n')
        pos_semicolon = self._buffer.find(b';')
        statement     = None
        if pos_newline >= 0 and (pos_semicolon < 0 or pos_semicolon > pos_newline):
            statement = self._buffer[:pos_newline]
            self._buffer = self._buffer[pos_newline + 1:]
        elif pos_semicolon >= 0 and (pos_newline < 0 or pos_newline > pos_semicolon):
            statement = self._buffer[:pos_semicolon]
            self._buffer = self._buffer[pos_semicolon + 1:]
        elif one_shot:
            statement = self._buffer
            self._buffer = b''
        return statement
    def _parse_statement(self, statement: str) -> tuple:
        if not statement:
            return (None, None)
        
        tokenize = statement.strip().split(' ')
        if tokenize[0].lower() in BusyBox.COMMANDS:
            cmd = BusyBox.COMMANDS[tokenize[0]]()
            return cmd.execute(tokenize[1:])
        elif tokenize[0].lower() == 'help':
            if len(tokenize) > 1 and tokenize[1].lower() in BusyBox.COMMANDS:
                cmd = BusyBox.COMMANDS[tokenize[1]]()
                return (cmd.help(), [{'action': 'COMMAND_HELP', 'data': tokenize[1]}], 1)
            else:
                return (self.help(), [{'action': 'COMMAND_HELP', 'data': None}], 1)
        
        return ('{}: applet not found\n'.format(tokenize[0]),
            [{'action': 'APPLET_NOT_FOUND', 'data': tokenize[0]}],
            1
        )