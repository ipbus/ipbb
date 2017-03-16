#!/usr/bin/env python


def parseArgs():
    import argparse
    import os.path
    parser = argparse.ArgumentParser()
    parser.add_argument("device")
    parser.add_argument("bitfile")
    args = parser.parse_args()

    # Validate bitfile path
    bitpath = os.path.abspath(args.bitfile)
    if not os.path.exists(bitpath):
        parser.error('Aaaaargh!!!')

    if not os.path.splitext(bitpath)[-1].lower() == '.bit':
        parser.error('Aaaaargh!!! Not a bitfile!!')

    args.bitfile = bitpath

    # Validate 'device'
    tokens = args.device.split(':')
    if len(tokens) != 2:
        parser.error(
            'Device format error. Expected format: <target match>:<device>')

    args.target = tokens[0]
    args.device = tokens[1]

    return args


if __name__ == '__main__':
    args = parseArgs()

    # Logging is important
    import logging
    logging.basicConfig(level=logging.DEBUG)

    # Build vivado interface
    import tools.xilinx
    v = tools.xilinx.VivadoConsole()

    v.openHw()
    v.connect('localhost:3121')
    hw_targets = v.getHwTargets()

    matching_targets = [t for t in hw_targets if args.target in t]
    if len(matching_targets) == 0:
        raise RuntimeError('Target %s not found. Targets available %s: ' % (
            args.target, ', '.join(hw_targets)))

    if len(matching_targets) > 1:
        raise RuntimeError(
            'Multiple targets matching %s found. Prease refine your selection. Targets available %s: ' % (
                args.target, ', '.join(hw_targets)
            )
        )

    v.openHwTarget(matching_targets[0])

    devs = v.getHwDevices()

    if args.device not in devs:
        raise RuntimeError('Device %s not found. Devices available %s: ' % (
            args.device, ', '.join(devs)))

    v.programDevice(args.device, args.bitfile)
