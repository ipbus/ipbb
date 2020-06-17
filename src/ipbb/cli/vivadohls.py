from __future__ import print_function, absolute_import
# ------------------------------------------------------------------------------

# Modules
import click

import types

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
@vivadohls.command('make-project', short_help='Assemble the project from sources.')
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
@click.pass_context
def makeproject(ctx, *args, **kwargs):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import makeproject
    # makeproject(env, aToScript, aToStdout)
    return (ctx.command.name, makeproject, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('csynth', short_help='Run C-synthesis.')
@click.pass_obj
@click.pass_context
def synth(ctx, *args, **kwargs):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import csynth
    # synth(env)
    return (ctx.command.name, csynth, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('csim', short_help='Run C-synthesis.')
@click.pass_obj
@click.pass_context
def sim(ctx, *args, **kwargs):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import csim
    # sim(env)
    return (ctx.command.name, csim, args, kwargs)


# ------------------------------------------------------------------------------
@vivadohls.command('cosim', short_help='Run C-synthesis.')
@click.pass_obj
@click.pass_context
def cosim(ctx, *args, **kwargs):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import cosim
    # cosim(env)
    return (ctx.command.name, cosim, args, kwargs)
