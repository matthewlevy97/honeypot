from core.honeymodule import HoneyHandler
from core.honeyfs import HoneyFS

FILESYSTEM_NAME = 'IOT_FS'

class IOTFS(HoneyFS):
    def __init__(self, handler: HoneyHandler):
        super(IOTFS, self).__init__(FILESYSTEM_NAME, handler)