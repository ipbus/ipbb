
# Modules
import click

# from ..cmds import sim

# kIPExportDir = 'ipcores_sim'
import types

from os.path import join


# ------------------------------------------------------------------------------
@click.group('sim', short_help="Set up simulation projects.", chain=True)
@click.pass_obj
@click.option('-p', '--proj', metavar='<name>', default=None, help='Switch to <name> before running subcommands.')
def sim(env, proj):
    '''Simulation commands group'''
    # from ..cmds.sim import sim
    # sim(env, proj)
    pass

# ------------------------------------------------------------------------------
@sim.resultcallback()
@click.pass_obj
def process_sim(env, subcommands, proj):

    from ..cmds.sim import sim
    sim(env, proj)

    # Executed the chained commands
    for name, cmd, args, kwargs in subcommands:
        cmd(*args, **kwargs)


# ------------------------------------------------------------------------------
def sim_get_command_aliases(self, ctx, cmd_name):
    """
    Temporary hack for backward compatibility
    """
    rv = click.Group.get_command(self, ctx, cmd_name)
    if rv is not None:
        return rv
    if cmd_name == 'project':
        return click.Group.get_command(self, ctx, 'make-project')
    if cmd_name == 'fli':
        return click.Group.get_command(self, ctx, 'fli-eth')

sim.get_command = types.MethodType(sim_get_command_aliases, sim)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@sim.command('setup-simlib', short_help="Compile xilinx simulation libraries")
@click.option('-x', '--xilinx-simlib', 'aXilSimLibsPath', default=join('${HOME}', '.xilinx_sim_libs'), envvar='IPBB_SIMLIB_BASE', metavar='<path>', help='Xilinx simulation library target directory. The default value is overridden by IPBB_SIMLIB_BASE environment variable when defined', show_default=True)
@click.option('-f', '--force', 'aForce', is_flag=True, help="Force simlib compilation/check.")
@click.pass_obj
@click.pass_context
def setupsimlib(ctx, *args, **kwargs):
    """Generate the Vivado simulation libraries for the current simulator (modelsim, questasim)
    """
    from ..cmds.sim import setupsimlib
    return (ctx.command.name, setupsimlib, args, kwargs)

# ------------------------------------------------------------------------------
@sim.command('ipcores', short_help="Generate vivado sim cores for the current design.")
@click.option('-x', '--xilinx-simlib', 'aXilSimLibsPath', default=join('${HOME}', '.xilinx_sim_libs'), envvar='IPBB_SIMLIB_BASE', metavar='<path>', help='Xilinx simulation library target directory. The default value is overridden by IPBB_SIMLIB_BASE environment variable when defined', show_default=True)
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Vivado tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Vivado tcl commands to screen (dry run).")
@click.pass_obj
@click.pass_context
def ipcores(ctx, *args, **kwargs):
    '''
    Generate the vivado libraries and cores required to simulate the current design.

    '''
    from ..cmds.sim import ipcores
    return (ctx.command.name, ipcores, args, kwargs)


# ------------------------------------------------------------------------------
@sim.command('fli-eth')
@click.option('-d', '--dev', metavar='DEVICE', default='tap0', help='Virtual network device')
@click.option('-i', '--ipbuspkg', metavar='IPBUSPACKAGE', default='ipbus-firmware', help='ipbus firmware package')
@click.pass_obj
@click.pass_context
def fli_eth(ctx, *args, **kwargs):
    """
    Build the Modelsim-ipbus foreign language interface
    """
    from ..cmds.sim import fli_eth
    return (ctx.command.name, fli_eth, args, kwargs)

# ------------------------------------------------------------------------------
@sim.command('fli-udp')
@click.option('-p', '--port', metavar='PORT', default='50001', help='UPD interface port')
@click.option('-i', '--ipbuspkg', metavar='IPBUSPACKAGE', default='ipbus-firmware', help='ipbus firmware package')
@click.pass_obj
@click.pass_context
def fli_udp(ctx, *args, **kwargs):
    """
    Build the Modelsim-ipbus foreign language interface
    """
    from ..cmds.sim import fli_udp
    return (ctx.command.name, fli_udp, args, kwargs)


# ------------------------------------------------------------------------------
@sim.command('make-project', short_help="Assemble the simulation project from sources")
@click.option('-o/-1', '--optimize/--single', 'aOptimise', default=True, help="Toggle sim script optimisation.")
@click.option('-s', '--to-script', 'aToScript', default=None, help="Write Modelsim tcl script to file and exit (dry run).")
@click.option('-o', '--to-stdout', 'aToStdout', is_flag=True, help="Print Modelsim tcl commands to screen and exit (dry run).")
@click.pass_obj
@click.pass_context
def makeproject(ctx, *args, **kwargs):
    """
    Creates the modelsim project

    \b
    1. Compiles the source code into the 'work' library,
    2. Generates a 'vsim' wrapper that sets the simulation environment before invoking vsim.

    NOTE: The ip/mac address of ipbus desings implementing a fli and exposing the ip/mac addresses via  top level generics can be set by defining the following user settings:

    \b
    - 'ipbus.fli.mac_address': mapped to MAC_ADDR top-level generic
    - 'ipbus.fli.ip_address': mapped to IP_ADDR top-level generic

    """
    from ..cmds.sim import makeproject
    return (ctx.command.name, makeproject, args, kwargs)

# ------------------------------------------------------------------------------
@sim.command()
@click.option('--dev', metavar='DEVICE', default='tap0', help='name of the new device')
@click.option('--ip', metavar='IP', default='192.168.201.1', help='ip address of the virtual interface')
@click.pass_obj
@click.pass_context
def virtualtap(ctx, *args, **kwargs):
    """VirtualTap
    """
    from ..cmds.sim import virtualtap
    return (ctx.command.name, virtualtap, args, kwargs)


# ------------------------------------------------------------------------------
@sim.command('mifs')
@click.pass_obj
@click.pass_context
def mifs(ctx, *args, **kwargs):
    """Import MIF files from project
    """
    from ..cmds.sim import mifs
    return (ctx.command.name, mifs, args, kwargs)

