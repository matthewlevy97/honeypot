from backends._busybox.busybox_command import BusyBoxCommand
from backends._busybox.wget import BusyBoxWget
from backends._busybox.echo import BusyBoxEcho
from core.honeybackend import HoneyShell
from core.honeymodule import HoneyHandler
from core.honeyfs import HoneyFSFileNotFound, HoneyFS
from config import config
import copy
import logging
import json

# TODO: Switch to gnu_getopt() ???

BACKEND_NAME = 'BusyBox'
logger = logging.getLogger(__name__)

COMMAND_HELP     = 'COMMAND_HELP'
APPLET_NOT_FOUND = 'APPLET_NOT_FOUND'
CMD_WHOAMI       = 'CMD_WHOAMI'
CMD_CD           = 'CMD_CD'
EXIT_SESSION     = 'EXIT_SESSION'
RUN_PROGRAM      = 'RUN_PROGRAM'

class BusyBox(HoneyShell):
    COMMANDS = {
        '/bin/ls':      None, # Populated in init
        '/bin/exit':    None, # Populated in init
        '/bin/logout':  None, # Populated in init
        '/bin/cd':      None, # Populated in init
        '/bin/whoami':  None, # Populated in init
        '/bin/sh':      None, # Populated in init
        '/bin/busybox': None, # Populated in init
        '/bin/echo':    BusyBoxEcho,
        '/bin/wget':    BusyBoxWget
    }
    def __init__(self, handler: HoneyHandler, user: str = 'root'):
        super(BusyBox, self).__init__(name=BACKEND_NAME,handler=handler, user=user)
        self._buffer = b''
        self._previous_return_value = 0
        self.commands = copy.deepcopy(BusyBox.COMMANDS)
        self.commands['/bin/ls']      = self._ls
        self.commands['/bin/exit']    = self._exit
        self.commands['/bin/logout']  = self._exit
        self.commands['/bin/cd']      = self._cd
        self.commands['/bin/whoami']  = self._whoami
        self.commands['/bin/sh']      = self._shell_recurse
        self.commands['/bin/busybox'] = self._shell_recurse
    def handle_input(self, data: bytes, one_shot: bool = False) -> dict:
        self._buffer += data.replace(b'\r', b'')
        
        statement = self._getStatement(one_shot)
        if not statement:
            while not statement and len(self._buffer) > 0:
                statement = self._getStatement(one_shot)
        
        ret_val      = 1
        exit_session = False
        output, actions, ret_val = self._parse_statement(statement.decode('utf-8'))
        for action in actions:
            if action['action'] == EXIT_SESSION:
                exit_session = True
            if type(action['data']) == str:
                self.addBackendAction(action['action'], action['data'])
            else:
                self.addBackendAction(action['action'], json.dumps(action['data']))

        self._previous_return_value = ret_val

        ret = {
            'success': statement != None,
            'output': output.encode('utf-8') if output else b'',
            'exit': exit_session
        }
        if ret['success'] and not ret['exit'] and not one_shot and len(self._buffer) > 0:
            recurse_ret = self.handle_input(b'', one_shot)
            ret['success'] = recurse_ret['success']
            ret['exit'] = recurse_ret['exit']
            ret['output'] += b'\r\n' + recurse_ret['output']
        return ret
    def help(self) -> str:
        ret = ''
        for command in self.commands:
            ret += '{}, '.format(command)
        if ret:
            return ret[:-2]
        return ret
    def get_prompt(self) -> str:
        return '\r\n{} # '.format(self.get_cwd())
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
    def _ls(self, shell: HoneyShell, opts: list) -> tuple:
        ret = '\r\n'
        for path in opts:
            _, directory = self._fs.get_file(path)
            if directory:
                if directory['type'] == HoneyFS.HONEYFS_DIRECTORY:
                    ret += '{}:\r\n'.format(path)
                    for fs_obj in directory['files']:
                        ret += '{}\r\n'.format(fs_obj['name'])
                else:
                    ret += '{}\r\n'.format(directory['name'])
            else:
                ret += 'ls: cannot access \'{}\': No such file or directory'.format(path)
        if len(opts) == 0:
            directory = self._fs.get_cwd()
            if directory:
                if directory['type'] == HoneyFS.HONEYFS_DIRECTORY:
                    for fs_obj in directory['files']:
                        ret += '{}\r\n'.format(fs_obj['name'])
                else:
                    ret += '{}\r\n'.format(directory['name'])
            else:
                ret += 'ls: cannot access \'{}\': No such file or directory'.format(path)
        return (ret, [], 0)
    def _exit(self, shell: HoneyShell, opts: list) -> tuple:
        return ('Exiting...', [{'action': EXIT_SESSION, 'data': self._session_id}], 0)
    def _whoami(self, shell: HoneyShell, opts: list) -> tuple:
        if len(opts) > 0:
            return ('''Usage: whoami

Print the user name associated with the current effective user id''', [], 1)
        return ('{}\r\n'.format(self.get_current_user()),
            [{'action': CMD_WHOAMI, 'data': self.get_current_user()}], 0)
    def _cd(self, shell: HoneyShell, opts: list) -> tuple:
        if len(opts) == 0:
            path = '/'
        else:
            path = opts[0]
        try:
            parent_dir, target_dir = self._fs.get_file(path)
        except HoneyFSFileNotFound:
            return ('{}: No such file or directory'.format(path), [], 1)
        
        if self._fs.set_cwd(target_dir):
            return (target_dir['name'], [{'action': CMD_CD, 'data': path}], 0)
        return ('{}: Not a directory'.format(path), [], 1)
    def _shell_recurse(self, shell: HoneyShell, opts: list) -> tuple:
        return self._parse_statement(' '.join(opts))
    def _parse_statement(self, statement: str) -> tuple:
        # Does not handle combining statements (ex '&&' and '||')
        # Does not handle IO redirection
        if not statement:
            return (None, [], 1)
        
        tokenize = statement.strip().split(' ')
        if tokenize[0].lower() == 'help':
            if len(tokenize) > 1 and tokenize[1].lower() in self.commands:
                cmd = self.commands[tokenize[1]]()
                return (cmd.help(), [{'action': COMMAND_HELP, 'data': tokenize[1]}], 1)
            else:
                return (self.help(), [{'action': COMMAND_HELP, 'data': None}], 1)
        
        for path in config['backends'][BACKEND_NAME]['env']['path']:
            executable = '{}{}'.format(path, tokenize[0]).lower()
            if executable in self.commands:
                try:
                    if issubclass(self.commands[executable], BusyBoxCommand):
                        cmd = self.commands[executable](self)
                        return cmd.execute(tokenize[1:])
                except TypeError:
                    pass
                if hasattr(self.commands[executable], '__call__'):
                    return self.commands[executable](self, tokenize[1:])
        
        try:
            _, fs_obj = self._fs.get_file(tokenize[0])
            if fs_obj and fs_obj['type'] == HoneyFS.HONEYFS_FILE:
                self._buffer = self._fs.read_file(fs_obj) + self._buffer
                return ('', [{'action': RUN_PROGRAM, 'data': tokenize[0]}], 0)
        except HoneyFSException:
            pass
        
        return ('{}: applet not found\n'.format(tokenize[0]),
            [{'action': APPLET_NOT_FOUND, 'data': tokenize[0]}],
            1
        )