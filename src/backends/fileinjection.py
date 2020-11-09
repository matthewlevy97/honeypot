from core.honeybackend import HoneyBackend
from core.honeymodule import HoneyHandler
from core.honeyfs import HoneyFSException, filesystem_collector
from config import config
import logging
import re

LFI_DETECTED = 'LFI_DETECTED'
RFI_DETECTED = 'RFI_DETECTED'

BACKEND_NAME = 'FileInjection'
logger = logging.getLogger(__name__)

class FileInjection(HoneyBackend):
    def __init__(self, handler: HoneyHandler):
        super(FileInjection, self).__init__(BACKEND_NAME, handler)
        self._fs = filesystem_collector.getFilesystem(
            config['backends'][BACKEND_NAME]['filesystem']
        )(self._handler)
    def handle_input(self, data: bytes, one_shot: bool = False) -> dict:
        success = False
        output  = b''
        actions = []

        # Check For LFI
        try:
            _, child = self._fs.get_file(data.decode('utf-8'))
            if child:
                actions.append({'action': LFI_DETECTED, 'data': data})
                success = True
                output += self._fs.read_file(child)
        except HoneyFSException as e:
            pass

        # Check for RFI
        pattern = re.compile(config['backends'][BACKEND_NAME]['rfi_pattern'])
        for match in pattern.findall(data):
            success = True
            out, acts = self._handle_rfi(match)
            output += out
            actions += acts
        
        for action in actions:
            self.addBackendAction(action['action'], action['data'])

        return {
            'success': success,
            'output': output
        }
    def _handle_rfi(self, url: bytes):
        actions = [{'action': RFI_DETECTED, 'data': url}]
        return (b'', actions)