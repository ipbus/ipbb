
# Modules
import click
import os
import ipbb
import subprocess

# Elements
from ..tools.common import SmartOpen
# from . import kProjAreaFile, kProjDir, ProjectInfo
# from ..cli.utils import DirSentry, raiseError, validateComponent
from ..cmds._utils import validateComponent
from ._utils import completeComponent, completeProject, completeDepFile

from os.path import join, split, exists, splitext, relpath, isdir


# ------------------------------------------------------------------------------
@click.group('proj', short_help="Create and manage projects.")
def proj():
    '''Create and manage firmware projects'''
    pass


# ------------------------------------------------------------------------------
# TODO: move the list of supported products somewhere else
@proj.command('create', short_help="Create a new project area.")
@click.argument('toolset', type=click.Choice(['vivado', 'sim', 'vivadohls']))
@click.argument('projname')
@click.argument('component', callback=validateComponent, autocompletion=completeComponent)
@click.argument('topdep', default='__auto__', autocompletion=completeDepFile('component'))
@click.pass_obj
def create(env, toolset, projname, component, topdep ):
    '''Creates a new area of name PROJNAME

      TOOLSET: Toolset used for the project areas, choices: vivado, sim

      PROJNAME: Name of the new project area

      COMPONENT: Component <package:component> contaning the top-level

      TOPDEP: Top dependency file.
    '''
    from ..cmds.proj import create
    create(env, toolset, projname, component, topdep)


# ------------------------------------------------------------------------------
@proj.command('ls', short_help="List projects in the current working area.")
@click.pass_obj
def ls( env ):
    '''Lists all available project areas
    '''
    from ..cmds.proj import ls
    ls(env)


# ------------------------------------------------------------------------------
@proj.command('cd', short_help="Change working directory.")
@click.option('-v', '--verbose', 'aVerbose', count=True, help="Command verbosity")
@click.argument( 'projname', autocompletion=completeProject )
@click.pass_obj
def cd( env, projname, aVerbose ):
    '''Changes current working directory (command line only)
    '''

    from ..cmds.proj import cd
    cd(env, projname, aVerbose)
