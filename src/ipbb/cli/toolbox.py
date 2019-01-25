from __future__ import print_function

import click

from .utils import validateComponent


# ------------------------------------------------------------------------------
@click.group('toolbox', short_help="Miscelaneous useful commands.")
@click.pass_obj
def toolbox(env):
    '''Miscelaneous useful commands'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    from impl.toolbox import toolbox
    toolbox(env)


# ------------------------------------------------------------------------------
@toolbox.command('check-dep', short_help="Performs basic checks on dependency files")
@click.option('-v', '--verbose', count=True)
@click.argument('component', callback=validateComponent)
@click.argument('depfile', required=False, default=None)
@click.option('-t', '--toolset', required=True, type=click.Choice(['vivado', 'sim']))
@click.pass_obj
def check_depfile(env, verbose, component, depfile, toolset):
    '''Perform basic checks on dependency files'''
    from impl.toolbox import check_depfile
    check_depfile(env, verbose, component, depfile, toolset)