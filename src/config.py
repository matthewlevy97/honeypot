import logging

config = {
    'SENSOR_VERSION': b'0.1',
    'SENSOR_NAME': b'testing',
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
            'backends': {
                'BusyBox'
            }
        }
    },
    'backends': {
        'BusyBox': {
            'description': 'BusyBox Emulator'
        }
    }
}