from config import config
from queue import Queue
import logging
import sqlite3
import threading

logger = logging.getLogger(__name__)

class Database(threading.Thread):
    THREAT_ENTRY                = 0
    THREAT_ACTION_ENTRY         = 1
    MODULE_ENTRY                = 2
    BACKEND_ENTRY               = 3
    BACKEND_ACTION_ENTRY        = 4
    FILESYSTEM_ENTRY            = 5
    FILESYSTEM_ACTION_ENTRY     = 6
    def __init__(self):
        super(Database, self).__init__()
        self._insert_queue = Queue()
    def create_database(self) -> None:
        c = self._conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS threats (
            threat_id TEXT PRIMARY KEY,
            module_id TEXT,
            src_ip    TEXT,
            src_port  INTEGER,
            dst_ip    TEXT,
            dst_port  INTEGER,
            FOREIGN KEY(module_id) REFERENCES modules(module_id)
        );''')
        c.execute('''CREATE TABLE IF NOT EXISTS threat_action (
            action_id INTEGER PRIMARY KEY AUTOINCREMENT,
            threat_id TEXT,
            action    TEXT,
            data      BLOB,
            FOREIGN KEY(threat_id) REFERENCES threats(threat_id)
        );''')
        c.execute('''CREATE TABLE IF NOT EXISTS backend_action (
            action_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            threat_id          TEXT,
            backend_id         TEXT,
            backend_session_id TEXT,
            action             TEXT,
            data               BLOB,
            FOREIGN KEY(threat_id) REFERENCES threats(threat_id),
            FOREIGN KEY(backend_id) REFERENCES backends(backend_id)
        );''')
        c.execute('''CREATE TABLE IF NOT EXISTS filesystem_action (
            action_id             INTEGER PRIMARY KEY AUTOINCREMENT,
            threat_id             TEXT,
            filesystem_id         TEXT,
            filesystem_session_id TEXT,
            action                TEXT,
            data                  BLOB,
            FOREIGN KEY(threat_id) REFERENCES threats(threat_id),
            FOREIGN KEY(filesystem_id) REFERENCES filesystems(filesystem_id)
        );''')
        c.execute('''CREATE TABLE IF NOT EXISTS modules (
            module_id          TEXT PRIMARY KEY,
            module_name        TEXT,
            module_description TEXT
        );''')
        c.execute('''CREATE TABLE IF NOT EXISTS backends (
            backend_id          TEXT PRIMARY KEY,
            backend_name        TEXT,
            backend_description TEXT
        );''')
        c.execute('''CREATE TABLE IF NOT EXISTS filesystems (
            filesystem_id          TEXT PRIMARY KEY,
            filesystem_name        TEXT,
            filesystem_description TEXT
        );''')
        self._conn.commit()
    def insertData(self, *args):
        self._insert_queue.put(args)
    def run(self):
        global logger

        self._conn = sqlite3.connect(config['database']['file'])
        self.create_database()

        while True:
            threat = self._insert_queue.get()
            print(threat)
            c = self._conn.cursor()
            if threat[0] == Database.THREAT_ENTRY:
                c.execute('''INSERT INTO threats
                VALUES
                (?,?,?,?,?,?)''', threat[1:])
            elif threat[0] == Database.THREAT_ACTION_ENTRY:
                c.execute('''INSERT INTO threat_action
                (threat_id, action, data)
                VALUES
                (?,?,?)''', threat[1:])
            elif threat[0] == Database.MODULE_ENTRY:
                c.execute('''INSERT OR IGNORE INTO modules
                VALUES
                (?,?,?)''', threat[1:])
            elif threat[0] == Database.BACKEND_ENTRY:
                c.execute('''INSERT OR IGNORE INTO backends
                VALUES
                (?,?,?)''', threat[1:])
            elif threat[0] == Database.BACKEND_ACTION_ENTRY:
                c.execute('''INSERT OR IGNORE INTO backend_action
                (threat_id, backend_id, backend_session_id, action, data)
                VALUES
                (?,?,?,?,?)''', threat[1:])
            elif threat[0] == Database.FILESYSTEM_ACTION_ENTRY:
                c.execute('''INSERT OR IGNORE INTO filesystem_action
                (threat_id, filesystem_id, filesystem_session_id, action, data)
                VALUES
                (?,?,?,?,?)''', threat[1:])
            elif threat[0] == Database.FILESYSTEM_ENTRY:
                c.execute('''INSERT OR IGNORE INTO filesystems
                VALUES
                (?,?,?)''', threat[1:])
            else:
                logger.debug('Invalid database table selected: {}'.format(threat[0]))
            self._conn.commit()

database = Database()