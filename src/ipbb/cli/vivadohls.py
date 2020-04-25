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
    from ..cmds.vivadohls import vivadohls
    vivadohls(env, proj, verbosity)


# ------------------------------------------------------------------------------
@vivadohls.command('make-project', short_help='Assemble the project from sources.')
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
def makeproject(env, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import makeproject
    makeproject(env, aToScript, aToStdout)

# ------------------------------------------------------------------------------
@vivadohls.command('synth', short_help='Run C-synthesis.')
@click.pass_obj
def synth(env):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import synth
    synth(env)


# ------------------------------------------------------------------------------
@vivadohls.command('sim', short_help='Run C-synthesis.')
@click.pass_obj
def sim(env):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import sim
    sim(env)


# ------------------------------------------------------------------------------
@vivadohls.command('cosim', short_help='Run C-synthesis.')
@click.pass_obj
def cosim(env):
    '''Make the Vivado project from sources described by dependency files.'''
    from ..cmds.vivadohls import cosim
    cosim(env)