from core.honeymodule import HoneyHandler
from core.db import database
from config import config
import logging
import hashlib
import uuid

logger = logging.getLogger(__name__)

class HoneyBackend(object):
    def __init__(self, name: str, handler: HoneyHandler, description: str = None):
        self._name = name
        if description:
            self._description = description
        else:
            self._description = config['backends'][name]['description']
        self._handler     = handler
        self._session_id  = uuid.uuid4().hex

        sha = hashlib.sha1()
        sha.update(config['SENSOR_NAME'])
        sha.update(self._name.encode('utf-8'))
        sha.update(self._description.encode('utf-8'))
        self._uid = sha.digest().hex()
        database.insertData(database.BACKEND_ENTRY, name, self._description, self._uid)
    def addBackendAction(self, key: str, value: bytes) -> bool:
        global logger
        if not self._handler.attack_id:
            logger.debug("Attached HoneyHandler must have created a new threat ID!")
            return False
        database.insertData(database.BACKEND_ACTION_ENTRY,
            self._handler.attack_id, self._uid, self._session_id,
            '{}_{}'.format(self._name, key), value
        )
        return True
    '''
    Returns:
    {
        'success': bool,
        'output': bytes
    }
    '''
    def handle_input(self, data: bytes, one_shot: bool = False) -> dict:
        raise NotImplementedError()
    def get_handler(self) -> HoneyHandler:
        return self._handler
    def get_name(self) -> str:
        return self._name
    def get_description(self) -> str:
        return self._description
    def get_uid(self) -> str:
        return self._uid
    def get_session_id(self) -> str:
        return self._session_id

class HoneyBackendCollector(object):
    def __init__(self):
        self._backends = {}
    def addBackend(self, backend_name: str, backend: HoneyBackend) -> bool:
        if not backend:
            return False
        self._backends[backend_name] = backend
        return True
    def getBackend(self, backend_name: str) -> HoneyBackend:
        if backend_name in self._backends:
            return self._backends[backend_name]
        return None

backend_collector = HoneyBackendCollector()