import getopt

class BusyBoxCommand(object):
    def __init__(self, name: str):
        self.name = name
    def parse(self, params: list, *args) -> tuple:
        try:
            args = getopt.getopt(params, *args)
        except:
            return (False, self.invalid_option(params, ''))
        return (True, args)
    def invalid_option(self, params: list, failed_option: str) -> str:
        raise NotImplementedError()
    def help(self) -> str:
        raise NotImplementedError()
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