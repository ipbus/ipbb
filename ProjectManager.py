#!/usr/bin/env python

'''
Usage:

will come at some point


'''

from __future__ import print_function
import argparse
import os
import logging

#---
class CliFactory(object):
    def __init__(self, plugins):
        self.parser = argparse.ArgumentParser(
            description='Assists in setting up a firmware build and simulation area',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )

        subparsers = self.parser.add_subparsers(dest = 'cmd')
        for cmd,cls in plugins.iteritems():
            cls.addArguments(subparsers,cmd)

        self._plugins = plugins

    def get(self):

        from os.path import dirname, realpath
        args = self.parser.parse_args()

        # Resolve current plugin
        plugin_cls = self._plugins[args.cmd]

        # Extract map
        vals = vars(args)

        # Enrich with current path
        vals['scriptpath'] = dirname(realpath(__file__))

        plugin = plugin_cls(**vals)

        return plugin

if __name__ == '__main__':

    from projmgr import WorkareaBuilder
    from projmgr.svn import CactusCreator, CactusProjectAdder, CactusFetcher, CactusCheckout
    from projmgr.vivado import VivadoAreaBuilder
    from projmgr.modelsim import ModelsimAreaBuilder

    plugins = {
        'create'   : CactusCreator,
        'addproj'  : CactusProjectAdder,
        'fetch'    : CactusFetcher,
        'checkout' : CactusCheckout,
        'buildarea': WorkareaBuilder,
        'sim'      : ModelsimAreaBuilder,
        'vivado'   : VivadoAreaBuilder,
    }

    cli_factory = CliFactory( plugins )
    plugin = cli_factory.get()

    plugin.execute()
    import sys; sys.exit(0)
    try:
        plugin.execute()
    except Exception as e:

        print('\n- ERROR ---\n',e)
