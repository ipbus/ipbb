# -*- coding: utf-8 -*-

# Modules
import click
from ._utils import completeProject
from ..depparser import dep_command_types


# ------------------------------------------------------------------------------
@click.group()
@click.pass_obj
@click.option('-p', '--proj', default=None, autocompletion=completeProject)
def dep(ictx, proj):
    '''Dependencies command group'''
    from ..cmds.dep import dep
    dep(ictx, proj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-p', '--pager', 'pager', help='Enable pager.', is_flag=True)
@click.option('-f', '--filter', 'filters', help='Select dep entries with regexes.', multiple=True)
def report(ictx, pager, filters):
    '''Summarise the dependency tree of the current project'''
    from ..cmds.dep import report
    report(ictx, pager, filters)


# ------------------------------------------------------------------------------
@dep.command('ls', short_help="List project files by group")
@click.argument('group', type=click.Choice(dep_command_types))
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def ls(ictx, group, output):
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
    ls(ictx, group, output)


# ------------------------------------------------------------------------------
@dep.command('components')
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def components(ictx, output):
    from ..cmds.dep import components
    components(ictx, output)


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.option('-v', '--verbose', count=True)
def hash(ictx, output, verbose):
    from ..cmds.dep import hash
    hash(ictx, output, verbose)


# ------------------------------------------------------------------------------
@dep.command()
@click.option('-t', '--tag', default=None, help="Optional tag to add to the archive name.")
@click.pass_obj
def archive(ictx, tag):
    from ..cmds.dep import archive
    archive(ictx, tag)
