from __future__ import print_function

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from ..tools.common import SmartOpen
from . import kProjAreaFile, kProjDir, ProjectInfo
from .utils import DirSentry, raiseError, validateComponent

from os.path import join, split, exists, splitext, relpath, isdir
from click import echo, style, secho


# ------------------------------------------------------------------------------
@click.group('proj', short_help="Create and manage projects.")
def proj():
    '''Create and manage firmware projects'''
    pass


# ------------------------------------------------------------------------------
# TODO: move the list of supported products somewhere else
@proj.command('create', short_help="Create a new project area.")
@click.argument('kind', type=click.Choice(['vivado', 'sim']))
@click.argument('projname')
@click.argument('component', callback=validateComponent)
@click.option('-t', '--topdep', default='top.dep', help='Top-level dependency file')
@click.pass_obj
def create( env, kind, projname, component, topdep ):
    '''Creates a new area of name PROJNAME of kind KIND

      KIND: Area kind, choices: vivado, sim

      PROJNAME: Name of the new project area

      COMPONENT: Component <package:component> contaning the top-level
    '''
    from impl.proj import create
    create(env, kind, projname, component, topdep)


# ------------------------------------------------------------------------------
@proj.command('ls', short_help="List projects in the current working area.")
@click.pass_obj
def ls( env ):
    '''Lists all available project areas
    '''
    from impl.proj import ls
    ls(env)


# ------------------------------------------------------------------------------
@proj.command('cd', short_help="Change working directory.")
@click.option('-v', '--verbose', 'aVerbose', count=True, help="Command verbosity")
@click.argument( 'projname' )
@click.pass_obj
def cd( env, projname, aVerbose ):
    '''Changes current working directory (command line only)
    '''

    from impl.proj import cd
    cd(env, projname, aVerbose)
