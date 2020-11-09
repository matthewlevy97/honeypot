import logging

config = {
    'SENSOR_VERSION': b'0.1',
    'SENSOR_NAME': b'testing',
    'SENSOR_ISOLATE': False, # Allow outbound connections for file retrieval
    'SENSOR_OUTBOUND_USER_AGENT': 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.133 Mobile Safari/535.19',
    'artifacts': {
        'dir_name': '/var/threats',
        'dir_perms': 755
    },
    'database': {
        'file': 'honey.sql'
    },
    'logging': {
        'file': 'honey.log',
        'level': logging.WARNING
    },
    'modules': {
        'HTTPModule': {
            'description': 'HTTP Honeypot',
            'advertise_version': 'httpd',
            'default': {
                'address': '0.0.0.0',
                'port': 8080
            },
            'path_backends': [
            ],
            'param_backends': [
                'BusyBox',
                'FileInjection'
            ]
        },
        'TelnetModule': {
            'description': 'Simple Telnet Server',
            'advertise_version': 'Raspbian GNU/Linux 10',
            'default': {
                'address': '0.0.0.0',
                'port': 23
            },
            'shell_backend': 'BusyBox',
            'auth': {
                'attempts': 3,
                'usernames': ['admin'],
                'passwords': ['password'],
                'allow_after_fail': True
            }
        }
    },
    'backends': {
        'BusyBox': {
            'description': 'BusyBox Emulator',
            'filesystem': 'IOT_FS',
            'advertise_version': 'BusyBox v1.20.0 (2012-04-22 12:29:58 CEST) multi-call binary.',
            'env': {
                # Empty string needed to treat absolute paths first
                'path': ['', '/bin/']
            }
        },
        'FileInjection': {
            'description': 'Emulate file injection vulnerabilities (LFI/RFI)',
            'filesystem': 'IOT_FS',
            'rfi_pattern': b'(?:http[s]?|ftp)://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        }
    },
    'filesystem': {
        'outfile_dir':  'fs',
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