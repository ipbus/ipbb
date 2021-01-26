import pytest

import sys
import os

import ipbb.tools.xilinx as xilinx


@pytest.fixture(scope='module')
def check_vivado_env():
    """Summary
    
    Raises:
        RuntimeError: Description
    """
    print(os.environ['XILINX_VIVADO'])
    # raise RuntimeError('SSSS')


def test_autodetect(check_vivado_env):

    # Vivado:
    lVivadoVer='''
Vivado v2017.4 (64-bit)
SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
IP Build 2085800 on Fri Dec 15 22:25:07 MST 2017
Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.
'''

    lVivadoLabVer='''
Vivado Lab Edition v2017.4 (64-bit)
SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.
'''
    assert xilinx.vivado_console._parseversion(lVivadoVer) == ('Vivado','2017.4')
    assert xilinx.vivado_console._parseversion(lVivadoLabVer) == ('Vivado Lab Edition','2017.4')
