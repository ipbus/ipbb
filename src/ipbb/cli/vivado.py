from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click

import types

from ..tools.common import which

# ------------------------------------------------------------------------------
def ensureVivado(env):
    if env.currentproj.settings['toolset'] != 'vivado':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivado', found '%s'" % env.currentproj.settings['toolset'])

    if not which('vivado'):
        # if 'XILINX_VIVADO' not in os.environ:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing.")
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.group('vivado', short_help='Set up, syntesize, implement Vivado projects.', chain=True)
@click.option('-p', '--proj', default=None, help="Selected project, if not current")
@click.option('-q', '--quiet', is_flag=True, default=False, help="Suppress most of Vivado messages")
@click.pass_context
def vivado(ctx, proj, quiet):
    '''Vivado command group'''
    from impl.vivado import vivado
    vivado(ctx, proj, quiet)


# ------------------------------------------------------------------------------
def vivado_get_command_aliases(self, ctx, cmd_name):
    """
    Temporary hack for backward compatibility
    """
    rv = click.Group.get_command(self, ctx, cmd_name)
    if rv is not None:
        return rv
    if cmd_name == 'project':
        return click.Group.get_command(self, ctx, 'make-project')

vivado.get_command = types.MethodType(vivado_get_command_aliases, vivado)


# ------------------------------------------------------------------------------
@vivado.command('make-project', short_help='Assemble the project from sources.')
@click.option('-r/-n', '--reverse/--natural', 'aReverse', default=True)
@click.option('-o/-1', '--optimize/--single', 'aOptimise', default=True, help="Toggle project script optimisation.")
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
def makeproject(env, aReverse, aOptimise, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''
    from impl.vivado import makeproject
    makeproject(env, aReverse, aOptimise, aToScript, aToStdout)


# ------------------------------------------------------------------------------
@vivado.command('check-syntax', short_help='Run the synthesis step on the current project.')
@click.pass_obj
def checksyntax(env):
    from impl.vivado import checksyntax
    checksyntax(env)


# -------------------------------------
@vivado.command('synth', short_help='Run the synthesis step on the current project.')
@click.option('-j', '--jobs', 'aNumJobs', type=int, default=None, help="Number of parallel jobs")
@click.option('-i', '--status-update-interval', 'aUpdateInt', type=int, default=1, help="Interal between status updates in minutes")
@click.pass_obj
def synth(env, aNumJobs, aUpdateInt):
    '''Run synthesis'''
    from .impl.vivado import synth
    synth(env, aNumJobs, aUpdateInt)



# ------------------------------------------------------------------------------
@vivado.command('impl', short_help='Run the implementation step on the current project.')
@click.option('-j', '--jobs', type=int, default=None)
@click.pass_obj
def impl(env, jobs):
    '''Launch an implementation run'''
    '''Run synthesis'''
    from impl.vivado import impl
    impl(env, jobs)


# # ------------------------------------------------------------------------------
# @vivado.command('order-constr', short_help='Change the order with which constraints are processed')
# @click.option('-i/-r', '--initial/--reverse', 'order', default=True, help='Reset or invert the order of evaluation of constraint files.')
# @click.pass_obj
# def orderconstr(env, order):
#     '''Reorder constraint set'''
#     from impl.vivado import orderconstr
#     orderconstr(env, order)

@vivado.command('resource-usage', short_help="Resource usage")
@click.pass_obj
def resource_usage(env):
    '''Create a resource_usage'''
    from impl.vivado import resource_usage
    resource_usage(env)

# ------------------------------------------------------------------------------
@vivado.command('bitfile', short_help="Generate the bitfile.")
@click.pass_obj
def bitfile(env):
    '''Create a bitfile'''
    from impl.vivado import bitfile
    bitfile(env)


# ------------------------------------------------------------------------------
@vivado.command('status', short_help="Show the status of all runs in the current project.")
@click.pass_obj
def status(env):
    '''Show the status of all runs in the current project.'''
    from impl.vivado import status
    status(env)


# ------------------------------------------------------------------------------
@vivado.command('reset', short_help="Reset synthesis and implementation runs.")
@click.pass_obj
def reset(env):
    '''Reset synth and impl runs'''

    from impl.vivado import reset
    reset(env)


# ------------------------------------------------------------------------------
@vivado.command('package', short_help="Package the firmware image and metadata into a standalone archive")
@click.pass_context
@click.option('--tag', '-t', 'aTag', default=None, help="Optional tag to add to the archive name.")
def package(ctx, aTag):
    '''Package bitfile with address table and file list

    '''
    from impl.vivado import package
    package(ctx, aTag)


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_context
def archive(ctx):
    from impl.vivado import archive
    archive(ctx)
