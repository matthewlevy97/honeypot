from backends._busybox.busybox_command import BusyBoxCommand
from core.honeybackend import HoneyShell
from config import config
import requests

INVALID_WGET_OPTION = 'INVALID_WGET_OPTION'
WGET_COMMAND_HELP   = 'WGET_COMMAND_HELP'
WGET_COMMAND_ARGS   = 'WGET_COMMAND_ARGS'
WGET_DOWNLOAD_URL   = 'WGET_DOWNLOAD_URL'

class BusyBoxWget(BusyBoxCommand):
    def __init__(self, shell: HoneyShell):
        super(BusyBoxWget, self).__init__('wget', shell)
    def invalid_option(self, params: list, failed_option: str) -> str:
        return ('''wget: invalid option -- '{}'
Usage: wget [OPTION]... [URL]...

Try `wget --help' for more options.
'''.format(failed_option), [
        {'action': INVALID_WGET_OPTION, 'data': params}
    ], 1)
    def help(self) -> str:
        return '''Usage: wget [-c|--continue] [-s|--spider] [-q|--quiet] [-O|--output-document FIL
E]                                                                              
        [--header 'header: value'] [-Y|--proxy on/off] [-P DIR]                 
        [--no-check-certificate] [-U|--user-agent AGENT] [-T SEC] URL...        
                                                                                
Retrieve files via HTTP or FTP                                                  
                                                                                
        -s      Spider mode - only check file existence                         
        -c      Continue retrieval of aborted transfer                          
        -q      Quiet                                                           
        -P DIR  Save to DIR (default .)                                         
        -T SEC  Network read timeout is SEC seconds                             
        -O FILE Save to FILE ('-' for stdout)                                   
        -U STR  Use STR for User-Agent header                                   
        -Y      Use proxy ('on' or 'off')'''
    def execute(self, params: list) -> tuple:
        actions = []
        success, args = self.parse(params, 'scqP:O:U:Y:T:', [
            'continue', 'spider', 'quiet', 'output-document=', 'header=',
            'proxy=', 'user-agent='
        ])
        if not success:
            return args
        
        if len(args[0]) == 0 and len(args[1]) == 0:
            return (self.help(), [{'action': WGET_COMMAND_HELP, 'data': 'wget'}], 1)
        
        actions.append({'action': WGET_COMMAND_ARGS, 'data': params})
        for url in args[1]:
            actions.append({'action': WGET_DOWNLOAD_URL, 'data': url})

            if not config['SENSOR_ISOLATE']:
                headers = {
                    'User-Agent': config['SENSOR_OUTBOUND_USER_AGENT'],
                }
                try:
                    req = requests.get(url, headers=headers)

                    filename  = req.request.path_url
                    real_path = '{}/{}/{}'.format(
                        config['artifacts']['dir_name'],
                        self.shell._session_id,
                        filename
                    )
                    fs_obj = self.shell._fs.create_file(filename, real_path)
                    cwd = self.shell._fs.get_cwd()
                    if not cwd:
                        pass
                    cwd['files'].append(fs_obj)
                    
                    self.shell._fs.write_file(fs_obj, req.content)
                except Exception as e:
                    print(e)
                    pass

        return ('', actions, 0)