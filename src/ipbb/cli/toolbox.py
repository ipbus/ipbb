from __future__ import print_function, absolute_import

import click

from ..cmds._utils import validateComponent, validateMultiplePackageOrComponents


# ------------------------------------------------------------------------------
@click.group('toolbox', short_help="Miscelaneous useful commands.")
@click.pass_obj
def toolbox(env):
    '''Miscelaneous useful commands'''
    from ..cmds.toolbox import toolbox
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
    from ..cmds.toolbox import check_depfile
    check_depfile(env, verbose, component, depfile, toolset)


@toolbox.command('vhdl-beautify', short_help="Beautifies VHDL files in components within an ipbb work area or standalone files/directories")
@click.option('-c', '--component', callback=validateMultiplePackageOrComponents, multiple=True)
@click.option('-p', '--path', type=click.Path(), multiple=True)
@click.pass_obj
def vhdl_beautify(env, component, path):
    '''Perform basic checks on dependency files
    
    Args:
        env (TYPE): Description
    '''
    from ..cmds.toolbox import vhdl_beautify
    vhdl_beautify(env, component, path)


