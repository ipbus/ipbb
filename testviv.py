#!/usr/bin/env python

# Logging is important
import logging
logging.basicConfig(level=logging.DEBUG)

# Build vivado interface
import xilinx.vivado
v = xilinx.vivado.Vivado()

v.openHw()
v.connect('localhost:3121')
hw_targets = v.getHwTargets()

if 'Digilent' not in hw_targets[0]:
    raise RuntimeError('Diligent programmer not found')

v.openHwTarget(hw_targets[0])

devs = v.getHwDevices()

if devs[0] != 'xc7k325t_0':
    raise RuntimeError('WTF?!? Where is my kintex7?')

v.programDevice(devs[0], '/net/home/ppd/thea/Development/ipbus/test/kc705_gmi/top/top.runs/impl_1/top.bit')

