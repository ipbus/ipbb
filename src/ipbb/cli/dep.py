# -*- coding: utf-8 -*-

# Modules
import click
from ._utils import completeProject
from ..depparser import dep_command_types


# ------------------------------------------------------------------------------
@click.group()
@click.pass_obj
@click.option('-p', '--proj', default=None, autocompletion=completeProject)
def dep(env, proj):
    '''Dependencies command group'''
    from ..cmds.dep import dep
    dep(env, proj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-f', '--filter', 'filters', help='Select dep entries with regexes.', multiple=True)
def report(env, filters):
    '''Summarise the dependency tree of the current project'''
    from ..cmds.dep import report
    report(env, filters)


# ------------------------------------------------------------------------------
@dep.command('ls', short_help="List project files by group")
@click.argument('group', type=click.Choice(dep_command_types))
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def ls(env, group, output):
    '''List project files by group

    \b
    - setup: Project setup scripts
    - src: Code files
    - hlssrc: HLS source files
    - addrtab: Address tables 
    - utils: Utility files
    - iprepo: IP repository
    
    '''

    from ..cmds.dep import ls
    ls(env, group, output)


# ------------------------------------------------------------------------------
@dep.command('components')
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def components(env, output):
    from ..cmds.dep import components
    components(env, output)


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.option('-v', '--verbose', count=True)
def hash(env, output, verbose):
    from ..cmds.dep import hash
    hash(env, output, verbose)


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
def archive(env):
    from ..cmds.dep import archive
    archive(env)
