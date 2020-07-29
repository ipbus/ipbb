from __future__ import print_function, absolute_import
# ------------------------------------------------------------------------------

# Modules
import click
import types
import importlib


# ------------------------------------------------------------------------------
@click.group('vivado', short_help='Set up, syntesize, implement Vivado projects.', chain=True)
@click.option('-p', '--proj', default=None, help="Selected project, if not current")
@click.option('-v', '--verbosity', type=click.Choice(['all', 'warnings-only', 'none']), default='all', help="Silence vivado messages")
@click.pass_obj
def vivado(env, proj, verbosity):
    '''Vivado command group
    
    \b
    Verbosity levels
    - all:
    - warnings-only:
    - none:
    '''
    # from ..cmds.vivado import vivado
    # vivado(env, proj, verbosity)
    pass

# ------------------------------------------------------------------------------
@vivado.resultcallback()
@click.pass_obj
def process_vivado(env, subcommands, proj, verbosity):

    from ..cmds.vivado import vivado
    vivado(env, proj, verbosity, (name for name,_,_,_ in subcommands))

    # Executed the chained commands
    for name, cmd, args, kwargs in subcommands:
        cmd(*args, **kwargs)

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
# @vivado.command('make-project', short_help='Assemble the project from sources.')
# @click.option('--enable-ip-cache/--disable-ip-cache', 'aEnableIPCache', default=False)
# @click.option('-o/-1', '--optimize/--single', 'aOptimise', default=True, help="Toggle project script optimisation.")
# @click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
# @click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
# @click.pass_obj
# def makeproject(env, aEnableIPCache, aOptimise, aToScript, aToStdout):
#     '''Make the Vivado project from sources described by dependency files.'''
#     from ..cmds.vivado import makeproject
#     makeproject(env, aEnableIPCache, aOptimise, aToScript, aToStdout)

# ------------------------------------------------------------------------------
@vivado.command('make-project', short_help='Assemble the project from sources.')
@click.option('--enable-ip-cache/--disable-ip-cache', 'aEnableIPCache', default=False)
@click.option('-o/-1', '--optimize/--single', 'aOptimise', default=True, help="Toggle project script optimisation.")
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
@click.pass_context
def makeproject(ctx, *args, **kwargs):
    '''Creates the Vivado project from sources.'''
    from ..cmds.vivado import makeproject
    return (ctx.command.name, makeproject, args, kwargs)


# # ------------------------------------------------------------------------------
# @vivado.command('check-syntax', short_help='Run the elaboration step on the current project.')
# @click.pass_obj
# def checksyntax(env):
#     from ..cmds.vivado import checksyntax
#     checksyntax(env)
# ------------------------------------------------------------------------------
@vivado.command('check-syntax', short_help='Run the elaboration step on the current project.')
@click.pass_obj
@click.pass_context
def checksyntax(ctx, *args, **kwargs):
    """Run Vivado syntax check on current project
    """
    from ..cmds.vivado import checksyntax
    return (ctx.command.name, checksyntax, args, kwargs)

# # -------------------------------------
# @vivado.command('synth', short_help='Run the synthesis step on the current project.')
# @click.option('-j', '--jobs', 'aNumJobs', type=int, default=None, help="Number of parallel jobs")
# @click.option('-i', '--status-update-interval', 'aUpdateInt', type=int, default=1, help="Interal between status updates in minutes")
# @click.pass_obj
# def synth(env, aNumJobs, aUpdateInt):
#     '''Run synthesis'''
#     from ..cmds.vivado import synth
#     synth(env, aNumJobs, aUpdateInt)

# -------------------------------------
@vivado.command('synth', short_help='Run the synthesis step on the current project.')
@click.option('-j', '--jobs', 'aNumJobs', type=int, default=None, help="Number of parallel jobs")
@click.option('-i', '--status-update-interval', 'aUpdateInt', type=int, default=1, help="Interal between status updates in minutes")
@click.pass_obj
@click.pass_context
def synth(ctx, *args, **kwargs):
    '''Run synthesis'''
    from ..cmds.vivado import synth
    return (ctx.command.name, synth, args, kwargs)

# ------------------------------------------------------------------------------
# @vivado.command('impl', short_help='Run the implementation step on the current project.')
# @click.option('-j', '--jobs', 'aNumJobs', type=int, default=None, help="Number of parallel jobs")
# @click.option('-s/-c', '--stop-on-timing-failure/--continue-on-timing-failure', 'aStopOnTimingErr', default=True)
# @click.pass_obj
# def impl(env, aNumJobs, aStopOnTimingErr):
#     '''Launch an implementation run'''
#     '''Run synthesis'''
#     from ..cmds.vivado import impl
#     impl(env, aNumJobs, aStopOnTimingErr)

# ------------------------------------------------------------------------------
@vivado.command('impl', short_help='Run the implementation step on the current project.')
@click.option('-j', '--jobs', 'aNumJobs', type=int, default=None, help="Number of parallel jobs")
@click.option('-s/-c', '--stop-on-timing-failure/--continue-on-timing-failure', 'aStopOnTimingErr', default=True)
@click.pass_obj
@click.pass_context
def impl(ctx, *args, **kwargs):
    '''Launch an implementation run'''
    from ..cmds.vivado import impl
    return (ctx.command.name, impl, args, kwargs)

# # ------------------------------------------------------------------------------
# @vivado.command('resource-usage', short_help="Resource usage")
# @click.pass_obj
# def resource_usage(env):
#     '''Create a resource_usage'''
#     from ..cmds.vivado import resource_usage
#     resource_usage(env)

# ------------------------------------------------------------------------------
@vivado.command('resource-usage', short_help="Resource usage")
@click.option('-c', '--cell', 'aCell', default=None, help="Submodule name")
@click.option('-d', '--depth', 'aDepth', type=int, default=1, help="Hierarchy depth")
@click.option('-f', '--file', 'aFile', type=click.Path(), default=None, help="Output file")
@click.pass_obj
@click.pass_context
def resource_usage(ctx, *args, **kwargs):
    '''Create a resource_usage'''
    from ..cmds.vivado import resource_usage
    return (ctx.command.name, resource_usage, args, kwargs)

# # ------------------------------------------------------------------------------
# @vivado.command('bitfile', short_help="Generate the bitfile.")
# @click.pass_obj
# def bitfile(env):
#     '''Create a bitfile'''
#     from ..cmds.vivado import bitfile
#     bitfile(env)

# ------------------------------------------------------------------------------
@vivado.command('bitfile', short_help="Generate the bitfile.")
@click.pass_obj
@click.pass_context
def bitfile(ctx, *args, **kwargs):
    '''Create a bitfile'''
    from ..cmds.vivado import bitfile
    return (ctx.command.name, bitfile, args, kwargs)

# ------------------------------------------------------------------------------
@vivado.command('memcfg', short_help="Generate the memcfg.")
@click.pass_obj
@click.pass_context
def memcfg(ctx, *args, **kwargs):
    '''Create a memcfg file for PROM programming
    
    Supports bin and mcs file types
    Requires the corresponding options to be defined in the dep files:
 
    * bin: 'binfile_options'  
    
    * mcs: 'mcsfile_options'
    '''
    from ..cmds.vivado import memcfg
    return (ctx.command.name, memcfg, args, kwargs)




# # ------------------------------------------------------------------------------
# @vivado.command('status', short_help="Show the status of all runs in the current project.")
# @click.pass_obj
# def status(env):
#     '''Show the status of all runs in the current project.'''
#     from ..cmds.vivado import status
#     status(env)

# ------------------------------------------------------------------------------
@vivado.command('status', short_help="Show the status of all runs in the current project.")
@click.pass_obj
@click.pass_context
def status(ctx, *args, **kwargs):
    '''Show the status of all runs in the current project.'''
    from ..cmds.vivado import status
    return (ctx.command.name, status, args, kwargs)


# # ------------------------------------------------------------------------------
# @vivado.command('reset', short_help="Reset synthesis and implementation runs.")
# @click.pass_obj
# def reset(env):
#     '''Reset synth and impl runs'''

#     from ..cmds.vivado import reset
#     reset(env)

# ------------------------------------------------------------------------------
@vivado.command('reset-runs', short_help="Reset synthesis and implementation runs.")
@click.pass_obj
@click.pass_context
def reset(ctx, *args, **kwargs):
    '''Reset synth and impl runs'''

    from ..cmds.vivado import reset
    return (ctx.command.name, reset, args, kwargs)


# # ------------------------------------------------------------------------------
# @vivado.command('package', short_help="Package the firmware image and metadata into a standalone archive")
# @click.pass_obj
# @click.option('--tag', '-t', 'aTag', default=None, help="Optional tag to add to the archive name.")
# def package(env, aTag):
#     '''Package bitfile with address table and file list

#     '''
#     from ..cmds.vivado import package
#     package(env, aTag)

# ------------------------------------------------------------------------------
@vivado.command('package', short_help="Package the firmware image and metadata into a standalone archive")
@click.option('--tag', '-t', 'aTag', default=None, help="Optional tag to add to the archive name.")
@click.pass_obj
@click.pass_context
def package(ctx, *args, **kwargs):
    '''Package bitfile with address table and file list

    '''
    from ..cmds.vivado import package
    return (ctx.command.name, package, args, kwargs)

# # ------------------------------------------------------------------------------
# @vivado.command()
# @click.pass_obj
# def archive(env):
#     from ..cmds.vivado import archive
#     archive(env)

# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
@click.pass_context
def archive(ctx, *args, **kwargs):
    from ..cmds.vivado import archive
    return (ctx.command.name, archive, args, kwargs)
