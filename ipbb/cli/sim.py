from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import subprocess
import sys
import sh
import shutil
import tempfile
import getpass

# Elements
from os.path import join, split, exists, splitext, basename, dirname, abspath, expandvars
from click import echo, secho, style
from ..tools.common import which, mkdir, SmartOpen
from ..tools.mentor import autodetect
from .tools import DirSentry, ensureNoMissingFiles


kIPExportDir = 'ipcores_sim'

# ------------------------------------------------
class ModelsimNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ModelsimNotFoundError, self).__init__(message)
# ------------------------------------------------


# ------------------------------------------------------------------------------
@click.group('sim', short_help="Set up simulation projects.", chain=True)
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
@sim.command('ipcores', short_help="Generate vivado sim cores for the current design.")
@click.option('-o', '--output', default=None)
@click.option('-x', '--xilinx-simpath', default=join('${HOME}', '.xilinx_sim_libs'), envvar='IPBB_SIMLIB_BASE', metavar='<path>', help='Xilinx simulation library target directory', show_default=True)
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

    # Use compiler executable to detect Modelsim's flavour
    lSimVariant = autodetect()
    # For questa and modelsim the simulator name is the variant name in lowercase
    lSimulator = lSimVariant.lower()
    echo(style(lSimVariant, fg='blue')+" detected")

    lDepFileParser = env.depParser

    # Store the target path in the env, for it to be retrieved by Vivado
    lSimlibPath = expandvars(join(xilinx_simpath, basename(os.environ['XILINX_VIVADO'])))

    echo ("Using Xilinx simulation library path: " + style(lSimlibPath, fg='blue'))

    lIPCores = []
    for src in reversed(lDepFileParser.CommandList["src"]):
        lPath, lBasename = os.path.split(src.FilePath)
        lName, lExt = os.path.splitext(lBasename)

        if lExt not in [".xci", ".edn"]:
            continue

        lIPCores.append(lBasename)

    if not lIPCores:
        secho ("WARNING: No ipcore files detected in this project", fg='yellow')
        # return
    else:
        echo ('List of cores in project')
        for lIPCore in lIPCores:
            echo('- ' + style(lIPCore, fg='blue'))

    from ..depparser.IPCoresSimMaker import IPCoresSimMaker
    # For questa and modelsim the simulator name is the variant name in lowercase
    lIPCoreSimMaker = IPCoresSimMaker(env.pathMaker, lSimlibPath, lSimVariant, lSimulator, kIPExportDir)

    from ..tools.xilinx import VivadoOpen
    with (
        VivadoOpen(lSessionId) if not output 
        else SmartOpen(output if output != 'stdout' else None)
    ) as lTarget:
        lIPCoreSimMaker.write(
            lTarget,
            lDepFileParser.ScriptVariables,
            lDepFileParser.Components,
            lDepFileParser.CommandList,
            lDepFileParser.Libs,
            lDepFileParser.Maps
        )
        # lTarget('open_project top/top.xpr')
        # lTarget('export_simulation -force -simulator {} -lib_map_path  ~/.xilinx_sim_libs/2017.4/'.format(lSimulator))


    lIPSimDir = join(kIPExportDir,lSimulator)
    # Create the target directory for the code simulation
    mkdir(join(lIPSimDir, '{0}_lib'.format(lSimulator), 'work'))
    # and copy the simlibrary config file into it
    shutil.copy(join(lSimlibPath, 'modelsim.ini'), lIPSimDir)

    # Compile 
    sh.vsim(
        '-c', '-do', 'compile.do', '-do', 'exit',
        _cwd=lIPSimDir, 
        _out=sys.stdout,
        _err=sys.stderr
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
@click.option('--optimise/--line-by-line', 'aOptimize', default=True, help="Toggle sim script optimisation.")
@click.option('-s', '--script-path', 'aScriptPath', default=None, help="Path of the simulation macro file. By default a temporary file is used.")
@click.option('-n', '--dry-run', 'aDryRun', default=None, is_flag=True)
@click.pass_obj
def project(env, aOptimize, aScriptPath, aDryRun):
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

    # Use compiler executable to detect Modelsim's flavour
    lSimulator = mentor.autodetect().lower()

    lDepFileParser = env.depParser

    # Ensure thay all dependencies have been resolved
    ensureNoMissingFiles(env.project, lDepFileParser)

    from ..depparser.ModelSimProjectMaker import ModelSimProjectMaker
    lSimProjMaker = ModelSimProjectMaker(env.pathMaker, aOptimize)

    with (
        SmartOpen(
            # Write the vsim script to aScriptPath if defined
            aScriptPath if aScriptPath is not None 
            # write to a .tcl tempfile otherwise
            else tempfile.NamedTemporaryFile(suffix='.tcl')
            )
        ) as lTarget:

        lSimProjMaker.write(
            lTarget,
            lDepFileParser.ScriptVariables,
            lDepFileParser.Components,
            lDepFileParser.CommandList,
            lDepFileParser.Libs,
            lDepFileParser.Maps
        )

        if aDryRun:
            return

        try:
            from ..tools.mentor import ModelSimBatch
            ModelSimBatch(lTarget.path)
        except sh.ErrorReturnCode_255 as e:
            secho(str(e), fg='red')
            raise click.ClickException("Simulation compilation failed")


    # ----------------------------------------------------------
    # Collect the list of libraries generated by ipcores to add them to
    # modelsim.ini
    lSimLibDirectory = abspath(join(
            kIPExportDir, 
            lSimulator,
            '{0}_lib'.format(lSimulator),
            'msim'
        ))

    if exists( lSimLibDirectory ):
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

    pwd = getpass.getpass("[sudo] password for %s: " % getpass.getuser())
    with sh.contrib.sudo(password=pwd, _with=True):
    # with sh.contrib.sudo( _with=True):
        sh.openvpn('--mktun', '--dev', dev, _out=sys.stdout)
        sh.ifconfig(dev, 'up', ip, _out=sys.stdout)
        sh.chmod('a+rw', '/dev/net/tun', _out=sys.stdout)

# ------------------------------------------------------------------------------
