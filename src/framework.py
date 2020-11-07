from backends.busybox import BusyBox
from config import config
from core.honeybackend import backend_collector
from core.honeyrunner import HoneyServe
from core.db import database
from modules.http_server import HTTPModule
import logging
import os

logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename=config['logging']['file'], level=config['logging']['level'])

    # Add backends
    backend_collector.addBackend('BusyBox', BusyBox)

    # Add modules
    serve = HoneyServe()
    serve.addModule(HTTPModule())

    database.start()

    try:
        serve.run()
    except KeyboardInterrupt:
        logger.debug("Detected CTRL+C. Exiting...")
    logger.info("Honeypot Shut Down")

if __name__ == '__main__':
    main()