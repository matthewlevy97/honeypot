from core.honeymodule import HoneyHandler
from core.db import database
from config import config
from os import walk
import hashlib
import json
import logging
import uuid

logger = logging.getLogger(__name__)

class HoneyFSException(Exception):
    pass

class HoneyFSNotDirectory(HoneyFSException):
    def __init__(self, error_file: dict):
        self.error_file = error_file

class HoneyFSFileNotFound(HoneyFSException):
    def __init__(self, error_file: str):
        self.error_file = error_file

class HoneyFSFileAlreadyExists(HoneyFSException):
    def __init__(self, error_file: dict):
        self.error_file = error_file

class HoneyFS(object):
    HONEYFS_DIRECTORY    = 0
    HONEYFS_FILE         = 1
    WRITE_MODE_OVERWRITE = 0
    WRITE_MODE_APPEND    = 1
    def __init__(self, name: str, handler: HoneyHandler, path: str = None, description: str = None):
        self._name    = name
        self._handler = handler
        if description:
            self._description = description
        else:
            self._description = config['filesystem'][name]['description']
        if path:
            self._path = path
        else:
            self._path = config['filesystem'][name]['path']

        self._fs  = self.create_directory('/', self._path, True)
        self._cwd = self._fs
        self._modified = False

        sha = hashlib.sha1()
        sha.update(config['SENSOR_NAME'])
        sha.update(self._name.encode('utf-8'))
        sha.update(self._description.encode('utf-8'))
        self._uid = sha.digest().hex()
        self._session_id = uuid.uuid4().hex
        self._load_from_path(self._path)
        database.insertData(database.FILESYSTEM_ENTRY, name, self._description, self._uid)
    def get_cwd(self) -> dict:
        return self._cwd
    def set_cwd(self, new_cwd: dict) -> dict:
        if new_cwd and new_cwd['type'] == HoneyFS.HONEYFS_DIRECTORY:
            self._cwd = new_cwd
            return self._cwd
        return None
    def write_file(self, honey_file: dict, data: bytes, mode: int) -> bool:
        if honey_file['type'] != HoneyFS.HONEYFS_FILE:
            return False
        
        self._modified = True

        if mode == HoneyFS.WRITE_MODE_OVERWRITE:
            self._flush_write(honey_file, contents)
            return True
        if mode == HoneyFS.WRITE_MODE_APPEND:
            self._flush_write(honey_file, contents, True)
            return True
        return False
    def read_file(self, honey_file: dict, num_bytes: int = -1) -> bytes:
        contents = b''
        
        if honey_file['type'] != HoneyFS.HONEYFS_FILE:
            return contents
        
        with open(honey_file['real_path'], 'rb') as f:
            contents = f.read()
        if num_bytes >= 0:
            return contents[:num_bytes]
        else:
            return contents
    def addFilesystemAction(self, key: str, value: bytes) -> bool:
        global logger
        if not self._handler.attack_id:
            logger.debug("Attached HoneyHandler must have created a new threat ID!")
            return False
        database.insertData(database.FILESYSTEM_ACTION_ENTRY,
            self._handler.attack_id, self._uid, self._session_id,
            '{}_{}'.format(self._name, key), value
        )
        return True
    def taint_fs(self) -> None:
        self._modified = True
    def dump_filesystem(self) -> None:
        global logger
        # Only dump if modified
        if not self._modified:
            return
        
        fs_file = '{}/{}/{}'.format(
            config['artifacts']['dir_name'],
            self._handler.attack_id,
            config['filesystem']['outfile_name']
        )
        with open(fs_file, 'w') as f:
            json.dump(self._fs, f)
        logger.info('Dumped FS ({}) to {}!'.format(self._name, fs_file))
    def get_file(self, filename: str) -> tuple:
        filename = self.sanitize_path(filename)
        if not filename:
            return None, None

        if filename[0] == '/':
            cwd = self._fs
        else:
            cwd = self._cwd
        
        # Remove leading emptry string and actual filename to get list of directories
        fname_spl = list(filter(None, filename.split('/')))
        if len(fname_spl) == 0:
            return self._fs, self._fs
        
        for d_actual in fname_spl[:-1]:
            found = False
            for fs_obj in cwd['files']:
                if d_actual == fs_obj['name']:
                    if fs_obj['type'] != HoneyFS.HONEYFS_DIRECTORY:
                        raise HoneyFSNotDirectory(fs_obj)
                    cwd   = fs_obj
                    found = True
                    break
            if not found:
                raise HoneyFSFileNotFound(d_actual)
        for fs_obj in cwd['files']:
            if fs_obj['name'] == fname_spl[-1]:
                self.addFilesystemAction('GET_FILE', fs_obj['real_path'])
                return (cwd, fs_obj)
        return (cwd, None)
    def move_file(self, src_filename: str, dst_filename: str, copy: bool = False, overwrite: bool = False) -> bool:
        src_parent, src_actual = self.get_file(src_filename)
        dst_parent, dst_actual = self.get_file(dst_filename)

        if not src_parent or not src_actual or not dst_parent:
            self.addFilesystemAction(
                'MOVE_FILE_FAIL', json.dumps([src_filename, dst_filename])
            )
            return False
        if dst_actual:
            if not overwrite:
                raise HoneyFSFileAlreadyExists(dst_actual)
            else:
                dst_actual['files'].remove(dst_actual)
        if copy:
            src_actual = copy.deepcopy(src_actual)
        else:
            src_parent['files'].remove(src_actual)
        dst_parent['files'].append(src_actual)
        self.addFilesystemAction(
            'MOVE_FILE_SUCCESS', json.dumps([src_filename, dst_filename])
        )
        return True
    def create_directory(self, name: str, real_path: str, setup_create: bool = False) -> dict:
        ret = {'files': []}
        ret.update(self._create_general(HoneyFS.HONEYFS_DIRECTORY, name, real_path))
        if not setup_create:
            self.addFilesystemAction(
                'CREATE_DIRECTORY', json.dumps(ret)
            )
        return ret
    def create_file(self, name: str, real_path: str, setup_create: bool = False) -> dict:
        ret = self._create_general(HoneyFS.HONEYFS_FILE, name, real_path)
        if not setup_create:
            self.addFilesystemAction(
                'CREATE_FILE', json.dumps(ret)
            )
        return ret
    def sanitize_path(self, path: str) -> str:
        if not path:
            return None
        path_spl = path.split('/')
        i = 0
        while i < len(path_spl):
            if path_spl[i] == '.':
                path_spl.pop(i)
                i -= 1
            elif path_spl[i] == '..':
                path_spl.pop(i)
                i -= 1
                if len(path_spl) > 0 and i > 0:
                    path_spl.pop(i)
                    i -= 1
            i += 1
        path_spl = list(filter(None, path_spl))
        if len(path_spl) == 0:
            return '/'
        return ('/' if path[0] == '/' else '') + '/'.join(path_spl)
    def _flush_write(self, honey_file: dict, contents: bytes, append: bool = False) -> None:
        fs_file = '{}/{}/{}/{}'.format(
            config['artifacts']['dir_name'],
            self._handler.attack_id,
            config['filesystem']['outfile_dir'],
            honey_file['file_id']
        )
        if append:
            f = open(fs_file, 'ab')
        else:
            f = open(fs_file, 'wb')
        f.write(contents)
        f.close()
    def _load_from_path(self, path: str) -> None:
        for (dirpath, dirnames, filenames) in walk(path):
            real_path = dirpath
            dirpath = dirpath[len(path):].split('/')
            if len(dirpath) > 0 and not dirpath[0]:
                dirpath = dirpath[1:]
            
            # Create all directories
            cwd = self._fs
            for d_actual in dirpath:
                target_file = None
                for fs_obj in cwd['files']:
                    if d_actual == fs_obj['name']:
                        if fs_obj['type'] != HoneyFS.HONEYFS_DIRECTORY:
                            raise HoneyFSFileAlreadyExists(fs_obj)
                        target_file = fs_obj
                        break
                if not target_file:
                    target_file = self.create_directory(d_actual, real_path, True)
                    cwd['files'].append(target_file)
                cwd = target_file

            # Add files
            for filename in filenames:
                cwd['files'].append(
                    self.create_file(filename, '{}/{}'.format(real_path, filename), True)
                )
    def _create_general(self, ftype: int, name: str, real_path: str, user: str = None, group: str = None, perms: int = 0):
        if not user:
            user = config['filesystem']['default']['user']
        if not group:
            group = config['filesystem']['default']['group']
        if perms == 0:
            perms = config['filesystem']['default']['perms']
        return {
            'file_id':   uuid.uuid4().hex,
            'type':      ftype,
            'name':      name,
            'real_path': real_path,
            'user':      user,
            'group':     group,
            'perms':     perms
        }

class HoneyFSCollector(object):
    def __init__(self):
        self._filesystems = {}
    def addFilesystem(self, name: str, filesystem: HoneyFS) -> None:
        self._filesystems[name] = filesystem
    def getFilesystem(self, name: str) -> HoneyFS:
        if name in self._filesystems:
            return self._filesystems[name]
        return None

filesystem_collector = HoneyFSCollector()