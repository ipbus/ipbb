#!/usr/bin/env python

import pprint
import yaml
from collections import OrderedDict


yaml_example="""

"""

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


x = d

pprint.pprint(x)
with open('required_packages.yml', 'w') as yaml_file:
    yaml.dump(d, yaml_file, default_flow_style=False)
print '\n'