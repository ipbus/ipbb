# Modules
import os

# Elements
from click import echo, style, secho
from ...tools.xilinx import VivadoOpen, VivadoConsoleError, VivadoSnoozer, VivadoOutputFormatter


# ------------------------------------------------------------------------------
def debug(ctx):
    pass


# ------------------------------------------------------------------------------
def dump(ctx):

    if 'IPBB_ROOT' in os.environ:
        echo(style('IPBB_ROOT', fg='blue') + ': ' + os.environ['IPBB_ROOT'])

    env = ctx.obj
    echo(style('src dir', fg='blue') + ': ' + env.srcdir)
    echo(style('proj dir', fg='blue') + ': ' + env.projdir)
    echo(style('project name', fg='blue') + ': ' + env.currentproj.name)


# ------------------------------------------------------------------------------
def ipy(ctx):
    '''Opens IPython to inspect the parser'''
    # env = ctx.obj

    import IPython

    IPython.embed()


# ------------------------------------------------------------------------------
def test_vivado_formatter(ctx):

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
def test_vivado_console(ctx):
    with VivadoOpen('debug') as lConsole:
        lConsole('puts "Hello Xilinx World"')
