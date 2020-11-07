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
            'advertise_version': 'httpd',
            'backends': {
                'BusyBox'
            }
        }
    },
    'backends': {
        'BusyBox': {
            'description': 'BusyBox Emulator',
            'advertise_version': 'BusyBox v1.20.0 (2012-04-22 12:29:58 CEST) multi-call binary.'
        }
    }
}