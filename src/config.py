import logging

config = {
    'SENSOR_VERSION': b'0.1',
    'SENSOR_NAME': b'testing',
    'artifacts': {
        'dir_name': 'threats/'
    },
    'database': {
        'file': 'honey.sql'
    },
    'logging': {
        'file': 'honey.log',
        'level': logging.DEBUG
    },
    'modules': {
        'HTTPModule': {
            'description': 'HTTP Honeypot',
            'advertise_version': 'httpd',
            'path_backends': [
            ],
            'param_backends': [
                'BusyBox',
                'FileInjection'
            ]
        }
    },
    'backends': {
        'BusyBox': {
            'description': 'BusyBox Emulator',
            'filesystem': 'IOT_FS',
            'advertise_version': 'BusyBox v1.20.0 (2012-04-22 12:29:58 CEST) multi-call binary.',
            'env': {
                # Empty string needed to treat absolute paths first
                'path': ['', '/bin']
            }
        },
        'FileInjection': {
            'description': 'Emulate file injection vulnerabilities (LFI/RFI)',
            'filesystem': 'IOT_FS',
            'rfi_pattern': b'(?:http[s]?|ftp)://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }
    },
    'filesystem': {
        'outfile_name': 'fs.json',
        'default': {
            'user': 'root',
            'group': 'root',
            'perms': 755
        },
        'IOT_FS': {
            'description': 'Emulated IOT FS',
            'path': 'filesystems/iot/'
        }
    }
}