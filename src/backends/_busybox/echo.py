from backends._busybox.busybox_command import BusyBoxCommand

class BusyBoxEcho(BusyBoxCommand):
    SPACES_IN_TAB = 4
    def __init__(self):
        super(BusyBoxEcho, self).__init__('echo')
    def help(self) -> str:
        return '''Usage: echo [-neE] [ARG...]

Print the specified ARGs to stdout

Options:

        -n      Suppress trailing newline
        -e      Interpret backslash-escaped characters (i.e., \\t=tab)
        -E      Disable interpretation of backslash-escaped characters
'''
    def invalid_option(self, params: list, failed_option: str) -> str:
        return (' '.join(params) + '\n',
            [{'action': 'INVALID_ECHO_OPTION', 'data': params}],
            1
        )
    def execute(self, params: list) -> tuple:
        success, args = self.parse(params, 'neE')
        if not success:
            return args

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
        return (output, [{'action': 'ECHO_OUTPUT', 'data': ' '.join(params)}], 0)
