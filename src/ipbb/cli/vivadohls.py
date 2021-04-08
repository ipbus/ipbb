
# Modules
import click

from ..utils import validateOptionalComponent
from ._utils import completeComponent

# import types

# ------------------------------------------------------------------------------
@click.group('vivado-hls', short_help='Set up, syntesize, implement VivadoHLS projects.', chain=True)
@click.option('-p', '--proj', default=None, help="Selected project, if not current")
@click.option('-v', '--verbosity', type=click.Choice(['all', 'warnings-only', 'none']), default='all', help="Silence vivado messages")
@click.pass_obj
def vivadohls(env, proj, verbosity):
    '''Vivado-HLS command group
    
    \b
    Verbosity levels
    - all:
    - warnings-only:
    - none:
    '''
    pass

# ------------------------------------------------------------------------------
@vivadohls.resultcallback()
@click.pass_obj
def process_vivadohls(env, subcommands, proj, verbosity):
    from ..cmds.vivadohls import vivadohls
    vivadohls(env, proj, verbosity)

    # Executed the chained commands
    for name, cmd, args, kwargs in subcommands:
        cmd(*args, **kwargs)

# ------------------------------------------------------------------------------
@vivadohls.command('generate-project', short_help='Assemble the project from sources.')
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
@click.pass_context
def genproject(ctx, *args, **kwargs):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import genproject
    return (ctx.command.name, genproject, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('csynth', short_help='Run C-synthesis.')
@click.pass_obj
@click.pass_context
def csynth(ctx, *args, **kwargs):
    '''Run C-synthesis.'''
    from ..cmds.vivadohls import csynth
    return (ctx.command.name, csynth, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('csim', short_help='Run C-simulation.')
@click.pass_obj
@click.pass_context
def csim(ctx, *args, **kwargs):
    '''Run C-simulation.'''
    from ..cmds.vivadohls import csim
    return (ctx.command.name, csim, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('cosim', short_help='Run Cosimulation.')
@click.pass_obj
@click.pass_context
def cosim(ctx, *args, **kwargs):
    '''Run Co-simulation.'''
    from ..cmds.vivadohls import cosim
    return (ctx.command.name, cosim, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('export-ip', short_help='Export ip repostory.')
@click.option('-c', '--to-component', callback=validateOptionalComponent, autocompletion=completeComponent)
@click.pass_obj
@click.pass_context
def export_ip(ctx, *args, **kwargs):
    '''Export the HLS ip as Xilinx ip catalog and XCI file.'''
    from ..cmds.vivadohls import export_ip
    return (ctx.command.name, export_ip, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('debug', short_help='Export ip repostory.')
@click.pass_obj
@click.pass_context
def debug(ctx, *args, **kwargs):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import debug
    return (ctx.command.name, debug, args, kwargs)