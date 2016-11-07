#!/usr/bin/env python

def parseArgs():
    import argparse
    import os.path
    parser = argparse.ArgumentParser()
    parser.add_argument("device")
    parser.add_argument("bitfile")
    args = parser.parse_args()

    bitpath = os.path.abspath(args.bitfile)
    if not os.path.exists(bitpath):
        raise RuntimeError('Aaaaargh!!!')

    if not os.path.splitext(bitpath)[-1].lower() == '.bit':
        raise RuntimeError('Aaaaargh!!! Not a bitfile!!')

    args.bitfile = bitpath
    return args

if __name__ == '__main__':
    args = parseArgs()

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

    if args.device not in devs:
        raise RuntimeError('WTF?!? Where is my kintex7?')

    v.programDevice(args.device, args.bitfile)
