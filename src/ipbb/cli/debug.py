# Modules
import click
import os

# Elements
from click import echo, style, secho
from ..tools.xilinx import VivadoOpen, VivadoConsoleError, VivadoSnoozer

# ------------------------------------------------------------------------------
@click.group()
@click.pass_context
def debug(ctx):
    pass
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('dump')
@click.pass_context
def dump(ctx):

    if 'IPBB_ROOT' in os.environ:
        echo(style('IPBB_ROOT', fg='blue')+': '+os.environ['IPBB_ROOT'])

    env = ctx.obj
    echo(style('src dir', fg='blue')+': '+env.srcdir)
    echo(style('proj dir', fg='blue')+': '+env.projdir)
    echo(style('project name', fg='blue')+': '+env.currentproj.name)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('ipy')
@click.pass_context
def ipy(ctx):
    '''Opens IPython to inspect the parser'''
    # env = ctx.obj

    import IPython
    IPython.embed()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('test-vivado-formatter')
@click.pass_context
def test_vivado_formatter(ctx):

    from ..tools.xilinx import VivadoOutputFormatter

    out = VivadoOutputFormatter('test | ')

    out.write('Plain\n')
    out.write('Start')
    out.write('End\n')

    out.write('Start')
    out.write('middle')
    out.write('End\n')
    out.write('INFO: this is an info message \n')
    out.write('WARNING: this is a warning message \n')
    out.write('CRITICAL WARNING: this is a critical warning message \n')
    out.write('ERROR: this is an error message \n')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('test-vivado-console')
@click.pass_context
def test_vivado_console(ctx):
    with VivadoOpen('debug') as lConsole:
        lConsole('puts Hello Xilinx World')
