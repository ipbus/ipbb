from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import subprocess
import sys

# Elements
from os.path import join, split, exists, splitext, basename, dirname, abspath, expandvars
from click import echo, secho, style
from ..tools.common import which, do, ensuresudo, SmartOpen
from .tools import DirSentry, ensureNoMissingFiles


# ------------------------------------------------
class ModelsimNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ModelsimNotFoundError, self).__init__(message)
# ------------------------------------------------


# ------------------------------------------------------------------------------
@click.group(chain=True)
@click.pass_context
@click.option('-p', '--proj', metavar='<name>', default=None, help='Switch to <name> before running subcommands.')
def sim(ctx, proj):
    '''Simulation commands'''
    if proj is None:
        return

    # Change directory before executing subcommand
    from .proj import cd
    ctx.invoke(cd, projname=proj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@sim.command('ipcores', short_help='Generate vivado sim cores for the current design.')
@click.option('-o', '--output', default=None)
@click.option('-x', '--xilinx-simpath', default=join('${HOME}', '.xilinx_sim_libs'), envvar='IPBB_SIMLIB_BASE', metavar='<path>', help='Library target directory', show_default=True)
@click.pass_obj
def ipcores(env, output, xilinx_simpath):
    '''
    Generate the vivado libraries and cores required to simulate the current design.
    '''


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

    lDepFileParser = env.depParser

    # Store the target path in the env, for it to be retrieved by Vivado
    simlibPath = expandvars(join(xilinx_simpath, basename(os.environ['XILINX_VIVADO'])))

    echo ('Using Xilinx simulation library path: ' + style(simlibPath, fg='blue'))

    for src in reversed(lDepFileParser.CommandList["src"]):
        lPath, lBasename = os.path.split(src.FilePath)
        lName, lExt = os.path.splitext(lBasename)

        if not (lExt == ".xci" or lExt == ".edn"):
            continue

        secho (lBasename, fg='blue')
    # raise SystemExit(0)

    from ..depparser.IPCoresSimMaker import IPCoresSimMaker
    lWriter = IPCoresSimMaker(env.pathMaker, simlibPath)

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
    sh.rm('-rf', 'modelsim_fli', 'mac_fli.so', _out=sys.stdout)
    # Copy
    sh.cp('-a', lFliSrc, './', _out=sys.stdout)
    # Make
    sh.make('-C', 'modelsim_fli', 'TAP_DEV={0}'.format(dev), _out=sys.stdout)
    # Link
    sh.ln('-s', 'modelsim_fli/mac_fli.so', '.', _out=sys.stdout)

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
            "Project area toolset mismatch. Expected 'sim', found '%s'" % env.projectConfig['toolset'])
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vsim'):
        raise click.ClickException(
            'ModelSim (vsim) not found. Please add Modelsim to PATH and execute the command again.')
    # -------------------------------------------------------------------------

    lDepFileParser = env.depParser

    # Ensure thay all dependencies have been resolved
    ensureNoMissingFiles(env.project, lDepFileParser)

    from ..depparser.ModelSimProjectMaker import ModelSimProjectMaker
    lWriter = ModelSimProjectMaker(env.pathMaker)

    from ..tools.mentor import ModelSimOpen, ModelSimConsoleError
    try:
        with (ModelSimOpen(lSessionId) if not output else SmartOpen(output if output != 'stdout' else None)) as lTarget:
            lWriter.write(
                lTarget,
                lDepFileParser.ScriptVariables,
                lDepFileParser.Components,
                lDepFileParser.CommandList,
                lDepFileParser.Libs,
                lDepFileParser.Maps
            )
    except ModelSimConsoleError as lExc:
        secho("Modelsim errors detected\n" +
              "\n".join(lExc.errors), fg='red'
              )
        raise click.Abort()
    except RuntimeError as lExc:
        secho("Error caught while generating ModelSim TCL commands:\n" +
              "\n".join(lExc), fg='red'
              )
        raise click.Abort()
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
    echo ('Detected simulation libraries: '+ style(', '.join(lSimLibs), fg='blue'))

    # add newly generated libraries to modelsim.ini
    echo ('Adding generated simulation libraries to modelsim.ini')
    import ConfigParser

    lModelsimIni = ConfigParser.RawConfigParser()
    lModelsimIni.read('modelsim.ini')
    for lSimLib in lSimLibs:
        echo (' - ' + lSimLib)
        lModelsimIni.set('Library', lSimLib, join(lSimLibDirectory, lSimLib))

    lLibSearchPaths = lModelsimIni.get('vsim', 'librarysearchpath').split() if  lModelsimIni.has_option('vsim', 'librarysearchpath') else []
    print (lLibSearchPaths)

    lLibSearchPaths += lSimLibs

    lNoDups = []
    for lSimLib in lLibSearchPaths:
        if lSimLib in lNoDups:
            continue
        lNoDups.append(lSimLib)
    # from collections import OrderedDict
    # lDummyDict = OrderedDict( ( (lLibPath, None) for lLibPath in lLibSearchPaths ) )

    lModelsimIni.set('vsim', 'librarysearchpath', ' '.join(lNoDups))

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
        lVsimSh('vsim "$@"')
        # lVsimSh('vsim {libs} "$@"'.format(
        #     libs=' '.join('-L ' + l for l in lSimLibs)))

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
