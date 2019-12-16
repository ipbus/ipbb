from __future__ import print_function, absolute_import
from future.utils import raise_with_traceback, raise_from
from future.utils import iterkeys, itervalues, iteritems
# ------------------------------------------------------------------------------

# Modules
import click
import os
import subprocess
import sys
import sh
import shutil
import getpass
import collections

import ipbb
import ipbb.tools.xilinx as xilinx
import ipbb.tools.mentor as mentor

# Elements
from os.path import (
    join,
    splitext,
    split,
    exists,
    splitext,
    basename,
    dirname,
    abspath,
    expandvars,
)
from click import echo, secho, style, confirm

# Tools imports
from ._utils import (
    DirSentry,
    ensureNoMissingFiles,
    echoVivadoConsoleError,
    getClickRootName,
    validateIpAddress,
    validateMacAddress,
)
from ..tools.common import which, mkdir, SmartOpen

# DepParser imports
from ..depparser.IPCoresSimMaker import IPCoresSimMaker
from ..depparser.SimlibMaker import SimlibMaker
from ..depparser.ModelSimProjectMaker import ModelSimProjectMaker


kIPExportDir = 'ipcores_sim'
kIPVivadoProjName = 'ipcores_proj'


# ------------------------------------------------------------------------------
def ensureModelsim(env):
    '''Utility function ensuring that the simulation environment is correctly setup'''

    if env.currentproj.settings['toolset'] != 'sim':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'sim', found '%s'"
            % env.currentproj.settings['toolset']
        )

    try:
        env.siminfo = mentor.autodetect()
    except mentor.ModelSimNotFoundError as lExc:
        raise raise_with_traceback(click.ClickException(str(lExc)))

    try:
        env.vivadoinfo = xilinx.autodetect()
    except xilinx.VivadoNotFoundError as lExc:
        env.vivadoinfo = None


# ------------------------------------------------------------------------------
def simlibPath(env, aBasePath):
    lSimVariant, lSimVersion = env.siminfo
    lVivadoVariant, lVivadoVersion = env.vivadoinfo

    return expandvars(
        join(
            aBasePath, lVivadoVersion, '{}_{}'.format(lSimVariant.lower(), lSimVersion)
        )
    )


# ------------------------------------------------------------------------------
def findIPSrcs( srcs ):
    return [
        split(name)[1]
        for name, ext in (
            splitext(src.FilePath) for src in srcs
        )
        if ext in [".xci"]
    ]


# ------------------------------------------------------------------------------
def sim(env, proj):
    '''Simulation commands group'''

    if proj is not None:
        # Change directory before executing subcommand
        from .proj import cd

        cd(env, projname=proj, aVerbose=False)
    else:
        if env.currentproj.name is None:
            raise click.ClickException(
                'Project area not defined. Move into a project area and try again.'
            )

    ensureModelsim(env)


# ------------------------------------------------------------------------------
def setupsimlib(env, aXilSimLibsPath, aToScript, aToStdout, aForce):
    lSessionId = 'setup-simlib'

    # -------------------------------------------------------------------------
    if not which('vivado'):
        raise click.ClickException(
            'Vivado is not available. Have you sourced the environment script?'
        )
    # -------------------------------------------------------------------------

    lDryRun = aToScript or aToStdout

    # Use compiler executable to detect Modelsim's flavour
    lSimVariant, lSimVersion = env.siminfo

    # For questa and modelsim the simulator name is the variant name in lowercase
    lSimulator = lSimVariant.lower()
    echo(style(lSimVariant, fg='blue') + " detected")

    # Guess the current vivado version from environment
    if env.vivadoinfo is None:
        raise click.ClickException(
            "Missing Vivado environment. Please source the veivado environment and try again"
        )

    lVivadoVariant, lVivadoVersion = env.vivadoinfo
    secho('Using Vivado version: ' + lVivadoVersion, fg='green')

    # -------------------------------------------------------------------------
    # Store the target path in the env, for it to be retrieved by Vivado
    # i.e. .xilinx_sim_libs/2017.4/modelsim_106.c
    lSimlibPath = simlibPath(env, aXilSimLibsPath)

    echo("Using Xilinx simulation library path: " + style(lSimlibPath, fg='blue'))

    lCompileSimlib = not exists(lSimlibPath) or aForce

    if not lCompileSimlib:
        echo(
            "Xilinx simulation library exist at {}. Compilation will be skipped.".format(
                lSimlibPath
            )
        )
    else:
        echo(
            "Xilinx simulation library will be generated at {}".format(
                style(lSimlibPath, fg='blue')
            )
        )

        lSimlibMaker = SimlibMaker(lSimulator, lSimlibPath)
        try:
            with (
                # Pipe commands to Vivado console
                xilinx.VivadoOpen(lSessionId)
                if not lDryRun
                else SmartOpen(
                    # Dump to script
                    aToScript
                    if not aToStdout
                    # Dump to terminal
                    else None
                )
            ) as lVivadoConsole:

                lSimlibMaker.write(lVivadoConsole)

        except xilinx.VivadoConsoleError as lExc:
            echoVivadoConsoleError(lExc)
            raise click.Abort()
        except RuntimeError as lExc:
            secho(
                "Error caught while generating Vivado TCL commands:\n"
                + "\n".join(lExc),
                fg='red',
            )
            raise click.Abort()

    shutil.copy(join(lSimlibPath, 'modelsim.ini'), '.')
    echo("\nmodelsim.ini imported from {}".format(lSimlibPath))


# ------------------------------------------------------------------------------
def ipcores(env, aXilSimLibsPath, aToScript, aToStdout):
    '''
    Generate the vivado libraries and cores required to simulate the current design.

    '''
    lSessionId = 'ipcores'
    lIPCoresModelsimIni = 'modelsim.ipcores.ini'

    lDryRun = aToScript or aToStdout

    # Use compiler executable to detect Modelsim's flavour
    lSimVariant, lSimVersion = env.siminfo
    lSimulator = lSimVariant.lower()

    if lSimulator in ['questasim']:
        lSimulator = 'questa'

    # For questa and modelsim the simulator name is the variant name in lowercase
    echo(style(lSimVariant, fg='blue') + " detected")
    secho('Using simulator: {} {}'.format(lSimVariant, lSimVersion), fg='green')

    # Guess the current vivado version from environment
    if env.vivadoinfo is None:
        raise click.ClickException(
            "Missing Vivado environment. Please source the veivado environment and try again"
        )

    lVivadoVariant, lVivadoVersion = env.vivadoinfo
    secho('Using Vivado version: ' + lVivadoVersion, fg='green')

    # -------------------------------------------------------------------------
    # Store the target path in the env, for it to be retrieved by Vivado
    # i.e. .xilinx_sim_libs/2017.4/modelsim_106.c
    lSimlibPath = simlibPath(env, aXilSimLibsPath)

    echo("Using Xilinx simulation library path: " + style(lSimlibPath, fg='blue'))

    if not exists(lSimlibPath):
        secho(
            "Warning: Simulation Xilinx libraries not found. Likely this is a problem.\nPlease execute {} sim setup-simlibs to generate them.".format(
                getClickRootName()
            ),
            fg='yellow',
        )
        confirm("Do you want to continue anyway?", abort=True)
    # -------------------------------------------------------------------------

    lDepFileParser = env.depParser

    lIPCores = findIPSrcs(lDepFileParser.commands["src"])

    if not lIPCores:
        secho("WARNING: No ipcore files detected in this project", fg='yellow')
        return
    else:
        echo('List of ipcores in project')
        for lIPCore in lIPCores:
            echo('- ' + style(lIPCore, fg='blue'))
    # -------------------------------------------------------------------------

    # For questa and modelsim the simulator name is the variant name in lowercase
    lIPCoreSimMaker = IPCoresSimMaker(env.currentproj, lSimlibPath, lSimulator, kIPExportDir, kIPVivadoProjName)

    secho("Generating ipcore simulation code", fg='blue')

    try:
        with (
            # Pipe commands to Vivado console
            xilinx.VivadoOpen(lSessionId)
            if not lDryRun
            else SmartOpen(
                # Dump to script
                aToScript
                if not aToStdout
                # Dump to terminal
                else None
            )
        ) as lVivadoConsole:

            lIPCoreSimMaker.write(
                lVivadoConsole,
                lDepFileParser.vars,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )
    except xilinx.VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        secho(
            "Error caught while generating Vivado TCL commands:\n" + "\n".join(lExc),
            fg='red',
        )
        raise click.Abort()

    # Copy the generated modelsim ini file locally, with a new name
    shutil.copy(
        join(lSimlibPath, 'modelsim.ini'), join(os.getcwd(), lIPCoresModelsimIni)
    )
    secho(
        "Imported modelsim.ini from {} to {}".format(lSimlibPath, lIPCoresModelsimIni),
        fg='blue',
    )

    # Prepare the area where to compile the simulation
    lIPSimDir = join(kIPExportDir, lSimulator)
    # Create the target directory for the code simulation
    mkdir(join(lIPSimDir, '{0}_lib'.format(lSimulator), 'work'))
    # and copy the simlibrary config file into it
    shutil.copy(join(lSimlibPath, 'modelsim.ini'), lIPSimDir)

    # Compile
    secho("Compiling ipcores simulation", fg='blue')

    with mentor.ModelSimBatch(echo=aToStdout, dryrun=lDryRun, cwd=lIPSimDir) as lSim:
        lSim('do compile.do')

    # ----------------------------------------------------------
    # Collect the list of libraries generated by ipcores to add them to
    # modelsim.ini
    lVivadoYear = [int(v) for v in lVivadoVersion.split('.')]

    if lVivadoYear[0] >= 2017:
        # Vivado 2017 requires an additional folder on the simulation path
        lCoreSimDir = abspath(
            join(kIPExportDir, lSimulator, '{0}_lib'.format(lSimulator), 'msim')
        )
    else:
        # Vivado 2016<
        lCoreSimDir = abspath(join(kIPExportDir, lSimulator, 'msim'))

    if not exists(lCoreSimDir):
        raise click.ClickException("Simlib directory not found")

    lSimLibs = next(os.walk(lCoreSimDir))[1]
    echo('Detected simulation libraries: ' + style(', '.join(lSimLibs), fg='blue'))

    # add newly generated libraries to modelsim.ini
    echo('Adding generated simulation libraries to modelsim.ini')
    from configparser import RawConfigParser

    lIniParser = RawConfigParser()
    lIniParser.read(lIPCoresModelsimIni, 'utf-8')
    for lSimLib in lSimLibs:
        echo(' - ' + lSimLib)
        lIniParser.set('Library', lSimLib, join(lCoreSimDir, lSimLib))

    lLibSearchPaths = (
        lIniParser.get('vsim', 'librarysearchpath').split()
        if lIniParser.has_option('vsim', 'librarysearchpath')
        else []
    )

    lLibSearchPaths += lSimLibs

    lNoDups = []
    for lSimLib in lLibSearchPaths:
        if lSimLib in lNoDups:
            continue
        lNoDups.append(lSimLib)

    lIniParser.set('vsim', 'librarysearchpath', ' '.join(lNoDups))

    # Make a backup copy of modelsim.ini (generated by ipcores)
    with SmartOpen('modelsim.ini') as newIni:
        lIniParser.write(newIni.target)


# ------------------------------------------------------------------------------
def fli_eth(env, dev, ipbuspkg):
    """
    Build the Modelsim-ipbus foreign language interface
    """

    # -------------------------------------------------------------------------
    if ipbuspkg not in env.sources:
        raise click.ClickException(
            "Package %s not found in source/. The FLI cannot be built." % ipbuspkg
        )

    # Set ModelSim root based on vsim's path
    os.environ['MODELSIM_ROOT'] = dirname(dirname(which('vsim')))
    # Apply set
    # os.environ['MTI_VCO_MODE']='64'

    lFliSrc = join(
        env.srcdir,
        ipbuspkg,
        'components',
        'modelsim_fli',
        'eth',
        'firmware',
        'sim',
        'modelsim_fli',
    )

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
def fli_udp(env, port, ipbuspkg):
    """
    Build the Modelsim-ipbus foreign language interface
    """

    # -------------------------------------------------------------------------
    if ipbuspkg not in env.sources:
        raise click.ClickException(
            "Package %s not found in source/. The FLI cannot be built." % ipbuspkg
        )

    # Set ModelSim root based on vsim's path
    os.environ['MODELSIM_ROOT'] = dirname(dirname(which('vsim')))
    # Apply set
    # os.environ['MTI_VCO_MODE']='64'

    lFliSrc = join(
        env.srcdir,
        ipbuspkg,
        'components',
        'modelsim_fli',
        'transport_udp',
        'firmware',
        'sim',
        'modelsim_fli',
    )

    import sh

    # Clean-up
    sh.rm('-rf', 'modelsim_fli', 'sim_udp_fli.so', _out=sys.stdout)
    # Copy
    sh.cp('-a', lFliSrc, './', _out=sys.stdout)
    # Make
    sh.make('-C', 'modelsim_fli', 'IP_PORT={0}'.format(port), _out=sys.stdout)
    # Link
    sh.ln('-s', 'modelsim_fli/sim_udp_fli.so', '.', _out=sys.stdout)


# ------------------------------------------------------------------------------
def makeproject(env, aOptimise, aToScript, aToStdout):
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

    lSessionId = 'project'

    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.currentproj.name is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again.'
        )

    if env.currentproj.settings['toolset'] != 'sim':
        raise click.ClickException(
            "Project area toolset mismatch. Expected 'sim', found '%s'"
            % env.currentproj.settings['toolset']
        )
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vsim'):
        raise click.ClickException(
            'ModelSim (vsim) not found. Please add Modelsim to PATH and execute the command again.'
        )
    # -------------------------------------------------------------------------

    # Use compiler executable to detect Modelsim's flavour
    # lSimulator = mentor.autodetect().lower()

    lDepFileParser = env.depParser

    # Ensure thay all dependencies have been resolved
    ensureNoMissingFiles(env.currentproj.name, lDepFileParser)

    lSimProjMaker = ModelSimProjectMaker(env.currentproj, kIPVivadoProjName, aOptimise)

    lDryRun = aToStdout or aToScript

    if not lDryRun:
        sh.rm('-rf', 'work')

    try:
        with mentor.ModelSimBatch(aToScript, echo=aToStdout, dryrun=lDryRun) as lSim:
            lSimProjMaker.write(
                lSim,
                lDepFileParser.vars,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )
    except sh.ErrorReturnCode as e:
        secho(
            'ERROR: Sim exit code: {}.\nCommand:\n\n   {}\n'.format(
                e.exit_code, e.full_cmd
            ),
            fg='red',
        )
        raise click.ClickException("Compilation failed")

    if lDryRun:
        return
    # ----------------------------------------------------------
    # Create a wrapper to force default bindings at load time
    print('Writing modelsim wrapper \'./vsim\'')

    lVsimArgs = collections.OrderedDict(
        [
            (
                'MAC_ADDR',
                validateMacAddress(
                    env.currentproj.usersettings.get('ipbus.fli.mac_address', None)
                ),
            ),
            (
                'IP_ADDR',
                validateIpAddress(
                    env.currentproj.usersettings.get('ipbus.fli.ip_address', None)
                ),
            ),
        ]
    )

    lVsimExtraArgs = ' '.join(
        ['-G{}=\'{}\''.format(k, v) for k, v in iteritems(lVsimArgs) if v is not None]
    )
    lVsimBody = '''#!/bin/sh

if [ ! -f modelsim.ini ]; then
    echo "WARNING: modelsim.ini not found. Vivado simulation libraries won't be loaded."
fi

export MTI_VCO_MODE=64
export MODELSIM_DATAPATH="mif/"
vsim {} "$@"
    '''.format(
        lVsimExtraArgs
    )
    with SmartOpen('vsim') as lVsimSh:
        lVsimSh(lVsimBody)

    # Make it executable
    os.chmod('vsim', 0o755)


# ------------------------------------------------------------------------------
def virtualtap(env, dev, ip):
    """VirtualTap
    """

    # -------------------------------------------------------------------------
    if not which('openvpn'):
        raise click.ClickException(
            'OpenVPN (openvpn) not found. Please install it and execute the command again.'
        )
    # -------------------------------------------------------------------------

    lCmds = '''
sudo openvpn --mktun --dev {0}
sudo /sbin/ifconfig {0} up {1}
sudo chmod a+rw /dev/net/tun
'''.format(
        dev, ip
    )

    pwd = getpass.getpass("[sudo] password for %s: " % getpass.getuser())
    with sh.contrib.sudo(password=pwd, _with=True):
        # with sh.contrib.sudo( _with=True):
        sh.openvpn('--mktun', '--dev', dev, _out=sys.stdout)
        sh.ifconfig(dev, 'up', ip, _out=sys.stdout)
        sh.chmod('a+rw', '/dev/net/tun', _out=sys.stdout)


def detectIPSimSrcs(projpath, ipcores):
    lSrcDir = abspath(join(projpath, kIPVivadoProjName, kIPVivadoProjName + '.srcs'))

    lIPPaths = {}
    for lIP in ipcores:

        lIPPaths[lIP] = None
        for lSubDir in ['', 'sim']:
            # Hack required. The Vivado generated hdl files sometimes
            # have 'sim' in their path, sometimes don't
            p = abspath(
                join(lSrcDir, 'sources_1', 'ip', lSubDir, lIP))

            if exists(p):
                lIPPaths[lIP] = p
                break

    return lIPPaths

# ------------------------------------------------------------------------------
def mifs(env):

    srcs = env.depParser.commands['src']

    # Seek mif files in sources
    lPaths = []
    for c in srcs:
        if splitext(c.FilePath)[1] != '.mif':
            continue
        lPaths.append(c.FilePath)

    if lPaths:
        sh.mkdir('-p', 'mif')
        for p in lPaths:
            echo('Copying {} to the project area'.format(p))
            sh.cp(p, 'mif/')

    # IPCores may generate mif files behinds the scenes
    lIPCores = [ f for f in findIPSrcs(srcs)]
    # lWorkingDir = abspath(join(env.currentproj.path, 'top'))

    lIPSrcs = detectIPSimSrcs(env.currentproj.path, lIPCores)

    lMissingIPSimSrcs = [ k for k, v in iteritems(lIPSrcs) if v is None]
    if lMissingIPSimSrcs:
        raise click.ClickException('Failed to collect mifs. Simulation sources not found for cores: {}'.format(', '.join(lMissingIPSimSrcs)))

    for c, d in iteritems(lIPSrcs):
        for file in os.listdir(d):
            if file.endswith(".mif"):
                p = os.path.join(d, file)
                echo('Copying {} to the project area'.format(p))
                sh.cp(p, '.')
