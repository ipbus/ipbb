# -*- coding: utf-8 -*-
from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click


# ------------------------------------------------------------------------------
@click.group()
@click.pass_context
@click.option('-p', '--proj', default=None)
def dep(ctx, proj):
    '''Dependencies command group'''
    from impl.dep import dep
    dep(ctx, proj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-f', '--filter', 'filters', help='Select dep entries with regexes.', multiple=True)
def report(env, filters):
    '''Summarise the dependency tree of the current project'''
    from impl.dep import report
    report(env, filters)


# ------------------------------------------------------------------------------
@dep.command('ls', short_help="List project files by group")
@click.argument('group', type=click.Choice(['setup', 'src', 'addrtab', 'cgpfile']))
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def ls(env, group, output):
    '''List project files by group

    - setup: Project setup scripts
    - src: Code files
    - addrtab: Address tables 
    - cgpfile: ?
    '''

    from impl.dep import ls
    ls(env, group, output)


# ------------------------------------------------------------------------------
@dep.command('components')
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def components(env, output):
    from impl.dep import components
    components(env, output)


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.option('-v', '--verbose', count=True)
def hash(env, output, verbose):
    from impl.dep import hash
    hash(env, output, verbose)


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_context
def archive(ctx):
    from impl.dep import archive
    archive(ctx)

