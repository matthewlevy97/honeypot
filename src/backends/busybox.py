from core.honeybackend import HoneyBackend
from core.honeymodule import HoneyHandler
from config import config
import getopt
import logging

BACKEND_NAME = 'BusyBox'
logger = logging.getLogger(__name__)

class BusyBoxCommand(object):
    def __init__(self, name: str):
        self.name = name
    '''
    (
        output,
        [
            {
                'action': str,
                'data': bytes
            }
        ]
    )
    '''
    def execute(self, params: list) -> tuple:
        raise NotImplementedError()

'''
echo
echo [-neE] [ARG...]

Print the specified ARGs to stdout

Options:

        -n      Suppress trailing newline
        -e      Interpret backslash-escaped characters (i.e., \t=tab)
        -E      Disable interpretation of backslash-escaped characters
'''
class BusyBoxEcho(BusyBoxCommand):
    SPACES_IN_TAB = 4
    def __init__(self):
        super(BusyBoxEcho, self).__init__('echo')
    def execute(self, params: list) -> tuple:
        try:
            args = getopt.getopt(params, 'neE')
        except:
            # Just return everything
            return (' '.join(params) + '\n', [])
        add_newline    = True
        interpret_tab  = False
        disable_interp = False
        for arg in args[0]:
            if arg[0] == '-n':
                add_newline = False
            elif arg[0] == '-e':
                interpret_tab = True
            elif arg[0] == '-E':
                disable_interp = True
        output = []
        for param in args[1]:
            if param.find('\\x') >= 0 and not disable_interp:
                try:
                    param = param.encode('utf-8').decode('unicode_escape')
                except Exception as e:
                    print(e)
                    pass
            if param.find('\\t') >= 0 and interpret_tab:
                param = param.replace('\\t', ' ' * BusyBoxEcho.SPACES_IN_TAB)
            output.append(param)
        output = ' '.join(output)
        if add_newline:
            output += '\n'
        return (output, [{'action': 'ECHO_OUTPUT', 'data': ' '.join(params)}])

class BusyBox(HoneyBackend):
    COMMANDS = {
        'echo': BusyBoxEcho
    }
    def __init__(self, handler: HoneyHandler):
        super(BusyBox, self).__init__(BACKEND_NAME, handler)
        self._buffer = b''
    def handle_input(self, data: bytes, one_shot: bool = False) -> dict:
        self._buffer += data
        
        statement = self._getStatement(one_shot)
        output, actions = self._parse_statement(statement.decode('utf-8'))
        for action in actions:
            self.addBackendAction(action['action'], action['data'])

        return {
            'success': statement != None,
            'output': output.encode('utf-8') if output else None
        }
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
        
        return ('{}: applet not found\n'.format(tokenize[0]),
            [{'action': 'APPLET_NOT_FOUND', 'data': tokenize[0]}]
        )