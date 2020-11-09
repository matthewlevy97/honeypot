from core.db import database
from config import config
import logging
import hashlib
import threading
import socket
import uuid

logger = logging.getLogger(__name__)

class HoneyModule(object):
    pass
class HoneyHandler(threading.Thread):
    def __init__(self, module: HoneyModule, server: socket.socket):
        self.module    = module
        self.server    = server
        self.attack_id = None
    def createThreat(self, src_ip: str, src_port: int, dst_ip: str, dst_port: int) -> None:
        self.attack_id = uuid.uuid4().hex
        database.insertData(database.THREAT_ENTRY,
            self.attack_id, self.module.get_uid(),
            src_ip, src_port, dst_ip, dst_port)
        logger.info('New Attack ID ({}) For Module ({})'.format(
            self.attack_id, self.module.get_uid()
        ))
    def createThreatFromSocket(self, sock: socket.socket) -> None:
        self.createThreat(sock.getpeername()[0], sock.getpeername()[1],
            sock.getsockname()[0], sock.getsockname()[1])
    def addThreatInfo(self, key: str, value: bytes) -> bool:
        global logger
        if not self.attack_id:
            logger.debug("Must call createThreat() first!")
            return False
        database.insertData(database.THREAT_ACTION_ENTRY, self.attack_id,
            '{}_{}'.format(self.module._name, key), value)
        return True
    def run(self) -> None:
        raise NotImplementedError()

class HoneyModule(object):
    def __init__(self, name: str, handler: HoneyHandler, description: str = None):
        self._name = name
        if description:
            self._description = description
        else:
            self._description = config['modules'][name]['description']
        self._handler = handler

        sha = hashlib.sha1()
        sha.update(config['SENSOR_NAME'])
        sha.update(self._name.encode('utf-8'))
        sha.update(self._description.encode('utf-8'))
        self._uid = sha.digest().hex()
        database.insertData(database.MODULE_ENTRY, name, self._description, self._uid)
    def bind_server(self) -> bool:
        raise NotImplementedError()
    def get_server(self) -> socket.socket:
        raise NotImplementedError()
    def get_handler(self) -> HoneyHandler:
        return self._handler
    def get_name(self) -> str:
        return self._name
    def get_description(self) -> str:
        return self._description
    def get_uid(self) -> str:
        return self._uid