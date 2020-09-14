
import click

from ..cmds._utils import validateComponent, validateMultiplePackageOrComponents
from ._utils import completeComponent, completeDepFile


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
@click.argument('toolset', type=click.Choice(['vivado', 'sim']))
@click.argument('component', callback=validateComponent, autocompletion=completeComponent)
@click.argument('depfile', required=False, default=None, autocompletion=completeDepFile('component'))
@click.pass_obj
def check_depfile(env, verbose, toolset, component, depfile):
    '''Perform basic checks on dependency files'''
    from ..cmds.toolbox import check_depfile
    check_depfile(env, verbose, toolset, component, depfile)


@toolbox.command('vhdl-beautify', short_help="Beautifies VHDL files in components within an ipbb work area or standalone files/directories")
@click.option('-c', '--component', callback=validateMultiplePackageOrComponents, autocompletion=completeComponent, multiple=True)
@click.option('-p', '--path', type=click.Path(), multiple=True)
@click.pass_obj
def vhdl_beautify(env, component, path):
    '''Perform basic checks on dependency files
    
    Args:
        env (TYPE): Description
    '''
    from ..cmds.toolbox import vhdl_beautify
    vhdl_beautify(env, component, path)


