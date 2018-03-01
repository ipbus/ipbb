#!/usr/bin/env python

import yaml
from collections import OrderedDict


d = {
    'ipbus-firmware': {
        'protocol': 'git',
        'uri': ''
    },
    'add': [
        {
            'uri': 'https://github.com/ipbus/ipbus-firmware.git',
            'protocol': 'git'
        },
        {
            'uri': 'https://github.com/ipbus/ipbus-firmware.git',
            'protocol': 'git'
        }
    ]
}


e = [
    [
        ('cmd', 'git'),
        ('repo', 'https://github.com/ipbus/ipbus-firmware.git'),
        ('branch', 'None'),
        ('dest', 'None'),
        ]
    
]

print e
with open('required_packages.yml', 'w') as yaml_file:
    yaml.dump(e, yaml_file, default_flow_style=False)
