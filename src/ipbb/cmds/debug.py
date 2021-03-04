# Modules
import os

# Elements
from click import echo, style, secho
from ..tools.xilinx import (
    VivadoSession,
    VivadoConsoleError,
    VivadoSnoozer,
    VivadoOutputFormatter,
)


# ------------------------------------------------------------------------------
def debug(ictx):
    pass


# ------------------------------------------------------------------------------
def dump(ictx):

    if 'IPBB_ROOT' in os.environ:
        echo(style('IPBB_ROOT', fg='blue') + ': ' + os.environ['IPBB_ROOT'])

    echo(style('src dir', fg='blue') + ': ' + ictx.srcdir)
    echo(style('proj dir', fg='blue') + ': ' + ictx.projdir)
    echo(style('project name', fg='blue') + ': ' + ictx.currentproj.name)


# ------------------------------------------------------------------------------
def ipy(ctx, ictx):
    '''Opens IPython to inspect the parser'''

    import IPython

    IPython.embed()


# ------------------------------------------------------------------------------
def test_vivado_formatter(ictx):

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
def test_vivado_console(ictx):
    with VivadoSession('debug') as lConsole:
        lConsole('puts "Hello Xilinx World"')
