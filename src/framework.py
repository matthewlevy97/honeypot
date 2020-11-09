from backends.busybox import BusyBox
from backends.fileinjection import FileInjection
from config import config
from core.honeybackend import backend_collector
from core.honeyrunner import HoneyServe
from core.honeyfs import filesystem_collector
from core.db import database
from filesystems.iot import IOTFS
from modules.http_server import HTTPModule
from modules.telnet_server import TelnetModule
import logging
import os

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename=config['logging']['file'], level=config['logging']['level'])

    # Add filesystems
    filesystem_collector.addFilesystem('IOT_FS', IOTFS)

    # Add backends
    backend_collector.addBackend('BusyBox', BusyBox)
    backend_collector.addBackend('FileInjection', FileInjection)

    # Add modules
    serve = HoneyServe()
    serve.addModule(HTTPModule())
    serve.addModule(TelnetModule())

    # Start database handler
    database.start()

    try:
        # Run modules
        serve.run()
    except KeyboardInterrupt:
        logger.debug("Detected CTRL+C. Exiting...")
    logger.info("Honeypot Shut Down")

if __name__ == '__main__':
    main()