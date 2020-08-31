
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
        return click.Group.get_command(self, ctx, 'generate-project')

vivado.get_command = types.MethodType(vivado_get_command_aliases, vivado)



# ------------------------------------------------------------------------------
@vivado.command('generate-project', short_help='Assemble the project from sources.')
@click.option('--enable-ip-cache/--disable-ip-cache', 'aEnableIPCache', default=False)
@click.option('-1', '--single', 'aOptimise', default=True, help="Disable project creation optimization. If present sources are added one at a time.")
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen and exit (dry run).")
@click.pass_obj
@click.pass_context
def genproject(ctx, *args, **kwargs):
    '''Creates the Vivado project from sources.'''
    from ..cmds.vivado import genproject
    return (ctx.command.name, genproject, args, kwargs)


# ------------------------------------------------------------------------------
@vivado.command('check-syntax', short_help='Run the elaboration step on the current project.')
@click.pass_obj
@click.pass_context
def checksyntax(ctx, *args, **kwargs):
    """Run Vivado syntax check on current project
    """
    from ..cmds.vivado import checksyntax
    return (ctx.command.name, checksyntax, args, kwargs)


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
@vivado.command('impl', short_help='Run the implementation step on the current project.')
@click.option('-j', '--jobs', 'aNumJobs', type=int, default=None, help="Number of parallel jobs")
@click.option('-s/-c', '--stop-on-timing-failure/--continue-on-timing-failure', 'aStopOnTimingErr', default=True)
@click.pass_obj
@click.pass_context
def impl(ctx, *args, **kwargs):
    '''Launch an implementation run'''
    from ..cmds.vivado import impl
    return (ctx.command.name, impl, args, kwargs)


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


# ------------------------------------------------------------------------------
@vivado.command('bitfile', short_help="Generate the bitfile.")
@click.pass_obj
@click.pass_context
def bitfile(ctx, *args, **kwargs):
    '''Create a bitfile'''
    from ..cmds.vivado import bitfile
    return (ctx.command.name, bitfile, args, kwargs)


# ------------------------------------------------------------------------------
@vivado.command('debug-probes', short_help="Generate (optional) debug-probes files (used for ILAs and VIO controls).")
@click.pass_obj
@click.pass_context
def bitfile(ctx, *args, **kwargs):
    '''Generate (optional) debug-probes files'''
    from ..cmds.vivado import debugprobes
    return (ctx.command.name, debugprobes, args, kwargs)


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


# ------------------------------------------------------------------------------
@vivado.command('status', short_help="Show the status of all runs in the current project.")
@click.pass_obj
@click.pass_context
def status(ctx, *args, **kwargs):
    '''Show the status of all runs in the current project.'''
    from ..cmds.vivado import status
    return (ctx.command.name, status, args, kwargs)


# ------------------------------------------------------------------------------
@vivado.command('reset-runs', short_help="Reset synthesis and implementation runs.")
@click.pass_obj
@click.pass_context
def reset(ctx, *args, **kwargs):
    '''Reset synth and impl runs'''

    from ..cmds.vivado import reset
    return (ctx.command.name, reset, args, kwargs)


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

# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
@click.pass_context
def archive(ctx, *args, **kwargs):
    from ..cmds.vivado import archive
    return (ctx.command.name, archive, args, kwargs)


@vivado.command()
@click.pass_obj
@click.pass_context
def ipy(ctx, *args, **kwargs):
    from ..cmds.vivado import ipy
    return (ctx.command.name, ipy, args, kwargs)

