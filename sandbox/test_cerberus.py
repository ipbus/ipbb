#!/usr/bin/env python
from __future__ import print_function, absolute_import

import cerberus
import yaml

schema_proj = {
    'name': {'type': 'string'},
    'toolset': {'type': 'string', 'allowed': ['vivado', 'vivado_hls', 'sim']},
    'topCmp': {'type': 'string'},
    'topDep': {'type': 'string'},
    'topPkg': {'type': 'string'},
    }

v = cerberus.Validator()

yaml_proj = '''
name: flx-fullchain
toolset: vivado
topCmp: projects/hitfinder
topDep: top_hf_fullchain.d3
topPkg: felix-pie
'''

doc_proj = yaml.safe_load(yaml_proj)

x = v.validate(doc_proj, schema_proj)
print('Proj Doc Validated', x)
print(v.errors)

yaml_setup = '''
init:
  - git submodule init
  - git submodule update

# reset is not yet supported
reset:
  - git submodule deinit -f .

# dependent repos, not yet implemented
repos:
  - name: ipbus
    type: git
    path: https://github.com/ipbus/ipbus-firmware.git
    branch: v1.6
  - name: dune-hitfinder
    type: git
    path: https://:@gitlab.cern.ch:8443/DUNE-SP-TDR-DAQ/dataflow-firmware.git
    branch: sponzio/hf_fullchainBash history saved
'''

doc_setup = yaml.safe_load(yaml_setup)

schema_setup = {
    'reset': {'type': 'list', 'schema': {'type': 'string'}},
    'init': {'type': 'list', 'schema': {'type': 'string'}},
}


x = v.validate(doc_setup, schema_setup)
print('Proj Doc Validated', x)
print(v.errors)
