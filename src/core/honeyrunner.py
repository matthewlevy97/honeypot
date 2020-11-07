from core.honeymodule import HoneyModule
import logging
import select
import socket

logger = logging.getLogger(__name__)

class HoneyServe(object):
    def __init__(self, timeout: int = 60):
        self._timeout     = timeout
        self._module_list = {}
    def addModule(self, module: HoneyModule) -> None:
        if module.get_uid() in self._module_list:
            return
        self._module_list[module.get_uid()] = module
    def removeModule(self, module: HoneyModule) -> None:
        self.removeModuleByUID(module.get_uid())
    def removeModuleByUID(self, uid: str) -> None:
        if uid in self._module_list:
            del self._module_list[uid]
    def run(self):
        global logger
        for module in self._module_list:
            logger.info('Binding Server For Module: {} ({})'.format(
                self._module_list[module].get_name(), module
            ))
            self._module_list[module].bind_server()
        
        threads = []
        while True:
            socks = [self._module_list[uid].get_server() for uid in self._module_list.keys()]
            readable, _, exceptional = select.select(socks, socks, socks, self._timeout)
            for s in readable:
                for uid in self._module_list.keys():
                    if self._module_list[uid].get_server() == s:
                        handler = self._module_list[uid].get_handler()
                        t = handler(self._module_list[uid], s)
                        t.run()
                        threads.append(t)
            for s in exceptional:
                for uid in self._module_list.keys():
                    if self._module_list[uid].get_server() == s:
                        self.removeModuleByUID(uid)