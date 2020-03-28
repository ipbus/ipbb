from __future__ import print_function, absolute_import

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
    xilinx.autodetect()
