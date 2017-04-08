from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from os.path import join, split, exists, splitext, basename, dirname, abspath
from ..tools.common import which, do, ensuresudo, SmartOpen
from .common import DirSentry


# ------------------------------------------------
class ModelsimNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ModelsimNotFoundError, self).__init__(message)
# ------------------------------------------------


# ------------------------------------------------------------------------------
@click.group(chain=True)
@click.pass_context
@click.option('-p', '--proj', default=None)
def sim(ctx, proj):
    '''Simulation command group'''
    if proj is None:
        return

    # Change directory before executing subcommand
    from .proj import cd
    ctx.invoke(cd, projname=proj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@sim.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def ipcores(env, output):
    lSessionId = 'ipcores'

    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

    if env.projectConfig['toolset'] != 'sim':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'sim', found '%s'" % env.projectConfig['toolset'])
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vivado'):
        # if 'XILINX_VIVADO' not in os.environ:
        raise click.ClickException(
            'Vivado is not available. Have you sourced the environment script?')
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vsim'):
        raise click.ClickException(
            'ModelSim is not available. Have you sourced the environment script?')
    # -------------------------------------------------------------------------

    # lDepFileParser, lPathmaker, lCommandLineArgs = makeParser( env, 3 )
    lDepFileParser = env.depParser

    from ..depparser.IPCoresSimMaker import IPCoresSimMaker
    lWriter = IPCoresSimMaker(env.pathMaker)

    # FIXME: Yeah, this is a hack
    # TODO: Remove XILINX_SIMLIBS reference from IPCoresSimMaker
    os.environ['XILINX_SIMLIBS'] = join(
        '.xil_sim_libs', basename(os.environ['XILINX_VIVADO']))

    from ..tools.xilinx import VivadoOpen
    with (VivadoOpen(lSessionId) if not output else SmartOpen(output if output != 'stdout' else None)) as lTarget:
        lWriter.write(
            lTarget,
            lDepFileParser.ScriptVariables,
            lDepFileParser.Components,
            lDepFileParser.CommandList,
            lDepFileParser.Libs,
            lDepFileParser.Maps
        )
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@sim.command()
@click.option('--dev', metavar='DEVICE', default='tap0', help='new virtual device')
@click.option('--ipbuspkg', metavar='IPBUSPACKAGE', default='ipbus-firmware', help='ipbus firmware package')
@click.pass_obj
def fli(env, dev, ipbuspkg):

    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

    if env.projectConfig['toolset'] != 'sim':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'sim', found '%s'" % env.projectConfig['toolset'])
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vsim'):
        raise click.ClickException(
            "ModelSim is not available. Have you sourced the environment script?")
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if ipbuspkg not in env.getSources():
        raise click.ClickException(
            "Package %s not found in source/. The FLI cannot be built." % ipbuspkg)
    # -------------------------------------------------------------------------

    # Set ModelSim root based on vsim's path
    os.environ['MODELSIM_ROOT'] = (dirname(dirname(which('vsim'))))
    # Apply set
    # os.environ['MTI_VCO_MODE']='64'

    lFliSrc = join(env.src, ipbuspkg, 'components', 'ipbus_eth',
                   'firmware', 'sim', 'modelsim_fli')

    import sh
    # Clean-up
    sh.rm('-rf', 'modelsim_fli', 'mac_fli.so')
    # Copy
    sh.cp('-a', lFliSrc, './')
    # Make
    sh.make('-C', 'modelsim_fli', 'TAP_DEV={0}'.format(dev))
    # Link
    sh.ln('-s', 'modelsim_fli/mac_fli.so', '.')

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@sim.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def project(env, output):
    lSessionId = 'project'

    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

    if env.projectConfig['toolset'] != 'sim':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'sim', found '%s'" % env.projectConfig['toolset'])
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vsim'):
        raise click.ClickException(
            'ModelSim (vsim) not found. Please add Modelsim to PATH and execute the command again.')
    # -------------------------------------------------------------------------

    # lDepFileParser, lPathmaker, lCommandLineArgs = makeParser( env, 3 )
    lDepFileParser = env.depParser

    from ..depparser.ModelSimProjectMaker import ModelSimProjectMaker
    lWriter = ModelSimProjectMaker(env.pathMaker)

    from ..tools.mentor import ModelSimOpen
    with (ModelSimOpen(lSessionId) if not output else SmartOpen(output if output != 'stdout' else None)) as lTarget:
        lWriter.write(
            lTarget,
            lDepFileParser.ScriptVariables,
            lDepFileParser.Components,
            lDepFileParser.CommandList,
            lDepFileParser.Libs,
            lDepFileParser.Maps
        )

    # ----------------------------------------------------------
    # FIXME: Tempourary assignments
    lWorkingDir = abspath(join(os.getcwd(), 'top'))
    # ----------------------------------------------------------

    # ----------------------------------------------------------
    # Collect the list of libraries generated by ipcores to add them to
    # modelsim.ini
    lSimLibDirectory = abspath(
        join(lWorkingDir, 'top.sim', 'sim_1', 'behav', 'msim'))
    lSimLibs = next(os.walk(lSimLibDirectory))[1]
    print ('Detected simulation libraries: ', ', '.join(lSimLibs))

    # add newly generated libraries to modelsim.ini
    print ('Adding generated simulation libraries to modelsim.ini')
    import ConfigParser

    lModelsimIni = ConfigParser.RawConfigParser()
    lModelsimIni.read('modelsim.ini')
    for lSimLib in lSimLibs:
        lModelsimIni.set('Library', lSimLib, join(lSimLibDirectory, lSimLib))

    # Make a backup copy of modelsim.ini (generated by ipcores)
    os.rename('modelsim.ini', 'modelsim.ini.bak')
    with SmartOpen('modelsim.ini') as newIni:
        lModelsimIni.write(newIni.file)

    # ----------------------------------------------------------
    # Create a wrapper to force default bindings at load time
    print ('Writing modelsim wrapper \'./vsim\'')
    with SmartOpen('vsim') as lVsimSh:
        lVsimSh('#!/bin/sh')
        lVsimSh('export MTI_VCO_MODE=64')
        lVsimSh('vsim {libs} "$@"'.format(
            libs=' '.join('-L ' + l for l in lSimLibs)))

    # Make it executable
    os.chmod('vsim', 0755)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@sim.command()
@click.option('--dev', metavar='DEVICE', default='tap0', help='name of the new device')
@click.option('--ip', metavar='IP', default='192.168.201.1', help='ip address of the virtual interface')
@click.pass_obj
def virtualtap(env, dev, ip):
    """VirtualTap
    """

    # -------------------------------------------------------------------------
    if not which('openvpn'):
        raise click.ClickException(
            'OpenVPN (openvpn) not found. Please install it and execute the command again.')
    # -------------------------------------------------------------------------

    lCmds = '''
sudo openvpn --mktun --dev {0}
sudo /sbin/ifconfig {0} up {1}
sudo chmod a+rw /dev/net/tun
'''.format(dev, ip)

    do(lCmds)
# ------------------------------------------------------------------------------
