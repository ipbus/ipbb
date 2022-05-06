# Modules
import click
import os
import subprocess
import sys
import sh
import shutil
import getpass
import collections
import cerberus

from copy import deepcopy
from rich.table import Table
from rich.prompt import Confirm

from .schema import project_schema, validate_schema

from ..console import cprint, console
from ..tools import xilinx, mentor
from ..utils import DEFAULT_ENCODING
from ..utils import ensureNoParsingErrors, ensureNoMissingFiles, logVivadoConsoleError
from ..utils import which, mkdir, SmartOpen
# Tools imports
from ..utils import DirSentry, ensureNoMissingFiles, logVivadoConsoleError, getClickRootName, validateIpAddress, validateMacAddress
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

# Generators imports
from ..generators.ipcoressim import IPCoresSimGenerator, find_ip_sim_src
from ..generators.modelsimproject import ModelSimGenerator

# Constants
kVsimWrapper = 'run_sim'
kIPExportDir = 'ipcores_sim'
kIPVivadoProjName = 'ipcores_proj'

_toolset='sim'
_schema = deepcopy(project_schema)
_schema.update({
    _toolset : {
        'schema': {
            'library' : {'type': 'string'},
            kVsimWrapper : {
                'schema': {
                    'design_units': {'type': 'string'},
                }
            }
        }
    }
})

# ------------------------------------------------------------------------------
def validate_settings(ictx):

    validate_schema(_schema, ictx.depParser.settings)



# ------------------------------------------------------------------------------
def ensure_modelsim(ictx):
    '''Utility function ensuring that the simulation environment is correctly setup'''

    if ictx.currentproj.settings['toolset'] != _toolset:
        raise click.ClickException(
            f"Work area toolset mismatch. Expected {_toolset}, found '{ictx.currentproj.settings['toolset']}'"
        )

    try:
        ictx.siminfo = mentor.autodetect()
    except mentor.ModelSimNotFoundError as lExc:
        tb = sys.exc_info()[2]
        raise click.ClickException(str(lExc)).with_traceback(tb)

    try:
        ictx.vivadoinfo = xilinx.autodetect()
    except xilinx.VivadoNotFoundError as lExc:
        ictx.vivadoinfo = None


# ------------------------------------------------------------------------------
def simlibPath(ictx, aBasePath):
    lSimVariant, lSimVersion = ictx.siminfo
    lVivadoVariant, lVivadoVersion = ictx.vivadoinfo

    return expandvars(
        join(
            aBasePath, lVivadoVersion, '{}_{}'.format(lSimVariant.lower(), lSimVersion)
        )
    )


# ------------------------------------------------------------------------------
def find_ip_src( srcs ):
    return [
        split(name)[1]
        for name, ext in (
            splitext(src.filepath) for src in srcs
        )
        if ext in ('.xci', '.xcix')
    ]


# ------------------------------------------------------------------------------
def sim(ictx, proj):
    '''Simulation commands group'''

    if proj is not None:
        # Change directory before executing subcommand
        from .proj import cd

        cd(ictx, projname=proj, aVerbose=False)

    if ictx.currentproj.name is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again.'
        )

    validate_settings
    (ictx)

    ensure_modelsim(ictx)


# ------------------------------------------------------------------------------
def setupsimlib(ictx, aXilSimLibsPath, aForce):
    lSessionId = 'setup-simlib'

    # -------------------------------------------------------------------------
    if not which('vivado'):
        raise click.ClickException(
            'Vivado is not available. Have you sourced the environment script?'
        )
    # -------------------------------------------------------------------------

    # Use compiler executable to detect Modelsim's flavour
    lSimVariant, lSimVersion = ictx.siminfo

    # For questa and modelsim the simulator name is the variant name in lowercase
    lSimulator = lSimVariant.lower()
    cprint(f"[blue]{lSimVariant}[/blue] detected")

    # Guess the current vivado version from environment
    if ictx.vivadoinfo is None:
        raise click.ClickException(
            "Missing Vivado environment. Please source the veivado environment and try again"
        )

    lVivadoVariant, lVivadoVersion = ictx.vivadoinfo
    cprint(f"Using Vivado version: {lVivadoVersion}", style='green')

    # -------------------------------------------------------------------------
    # Store the target path in the ictx, for it to be retrieved by Vivado
    # i.e. .xilinx_sim_libs/2017.4/modelsim_106.c
    lSimlibPath = simlibPath(ictx, aXilSimLibsPath)

    cprint(f"Using Xilinx simulation library path: [blue]{lSimlibPath}[/blue]")

    lCompileSimlib = not exists(lSimlibPath) or aForce

    if not lCompileSimlib:
        cprint(
            f"Xilinx simulation library exist at {lSimlibPath}. Compilation will be skipped."
        )
    else:
        cprint(
            f"Xilinx simulation library will be generated at [blue]{lSimlibPath}[/blue]"
        )

        try:
            with xilinx.VivadoSession(sid=lSessionId) as lVivadoConsole:
                lVivadoConsole(
                    'compile_simlib -verbose -simulator {} -family all -language all -library all -dir {{{}}}'.format(lSimulator, lSimlibPath)
                )

        except xilinx.VivadoConsoleError as lExc:
            logVivadoConsoleError(lExc)
            raise click.Abort()
        except RuntimeError as lExc:
            console.log(
                f"Error caught while generating Vivado TCL commands: {lExc}",
                style='red',
            )
            raise click.Abort()

    lModelsimIniPath = join(lSimlibPath, 'modelsim.ini')
    if not exists(lModelsimIniPath):
        raise click.ClickException(
            'Failed to locate modelsim.ini in the simlin target folder. This usually means that Vivado failed to compile the simulation libraries. Please check the logs.'
        )

    shutil.copy(join(lSimlibPath, 'modelsim.ini'), '.')
    cprint(f"modelsim.ini imported from {lSimlibPath}")


# ------------------------------------------------------------------------------
def ipcores(ictx, aXilSimLibsPath, aToScript, aToStdout):
    '''
    Generate the vivado libraries and cores required to simulate the current design.

    '''
    lSessionId = 'ipcores'
    lIPCoresModelsimIni = 'modelsim.ipcores.ini'

    lDryRun = aToScript or aToStdout
    lScriptPath = aToScript if not aToStdout else None

    # Use compiler executable to detect Modelsim's flavour
    lSimVariant, lSimVersion = ictx.siminfo
    lSimulator = lSimVariant.lower()

    if lSimulator in ['questasim']:
        lSimulator = 'questa'

    # For questa and modelsim the simulator name is the variant name in lowercase
    cprint(f"[blue]{lSimVariant}[/blue] detected")
    cprint(f'Using simulator: {lSimVariant} {lSimVersion}', style='green')

    # Guess the current vivado version from environment
    if ictx.vivadoinfo is None:
        raise click.ClickException(
            "Missing Vivado environment. Please source the veivado environment and try again"
        )

    lVivadoVariant, lVivadoVersion = ictx.vivadoinfo
    cprint(f"Using Vivado version: {lVivadoVersion}", style='green')

    # -------------------------------------------------------------------------
    # Store the target path in the ictx, for it to be retrieved by Vivado
    # i.e. .xilinx_sim_libs/2017.4/modelsim_106.c
    lSimlibPath = simlibPath(ictx, aXilSimLibsPath)

    cprint(f"Using Xilinx simulation library path: [blue]{lSimlibPath}[/blue]")

    if not exists(lSimlibPath):
        cprint(
            f"WARNING: Xilinx simulation libraries not found. Likely this is a problem.\nPlease execute {getClickRootName()} sim setup-simlibs to generate them.",
            style='yellow'
        )
        if not Confirm.ask("Do you want to continue anyway?"):
            return
    # -------------------------------------------------------------------------

    lDepFileParser = ictx.depParser

    # Ensure that no parsing errors are present
    ensureNoParsingErrors(ictx.currentproj.name, lDepFileParser)

    # Ensure that all dependencies are resolved
    ensureNoMissingFiles(ictx.currentproj.name, lDepFileParser)

    lIPCores = find_ip_src(lDepFileParser.commands["src"])

    if not lIPCores:
        cprint("WARNING: No ipcore files detected in this project", style='yellow')
        return
    else:
        cprint("List of ipcores in project")
        for lIPCore in lIPCores:
            cprint(f"- [blue]{lIPCore}[/blue]")
    # -------------------------------------------------------------------------

    # For questa and modelsim the simulator name is the variant name in lowercase
    lIPCoreSimMaker = IPCoresSimGenerator(ictx.currentproj, lSimlibPath, lSimulator, kIPExportDir, kIPVivadoProjName)

    cprint("Generating ipcore simulation code", style='blue')

    try:
        with (
            # Pipe commands to Vivado console
            xilinx.VivadoSession(sid=lSessionId) if not lDryRun
            else SmartOpen(lScriptPath)
        ) as lVivadoConsole:

            lIPCoreSimMaker.write(
                lVivadoConsole,
                lDepFileParser.settings,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )
    except xilinx.VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        cprint(
            f"Error caught while generating Vivado TCL commands: {lExc}",
            style='red',
        )
        raise click.Abort()

    # Copy the generated modelsim ini file locally, with a new name
    shutil.copy(
        join(lSimlibPath, 'modelsim.ini'), join(os.getcwd(), lIPCoresModelsimIni)
    )
    cprint(
        f"Imported modelsim.ini from {lSimlibPath} to {lIPCoresModelsimIni}",
        style='blue',
    )

    # Prepare the area where to compile the simulation
    lIPSimDir = join(kIPExportDir, lSimulator)
    # Create the target directory for the code simulation
    mkdir(join(lIPSimDir, '{0}_lib'.format(lSimulator), 'work'))
    # and copy the simlibrary config file into it
    shutil.copy(join(lSimlibPath, 'modelsim.ini'), lIPSimDir)

    # Compile
    cprint("Compiling ipcores simulation", style='blue')

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
    cprint(f"Detected simulation libraries: [blue]{lSimLibs}[/blue]")

    # add newly generated libraries to modelsim.ini
    cprint('Adding generated simulation libraries to modelsim.ini')
    from configparser import RawConfigParser

    lIniParser = RawConfigParser()
    lIniParser.read(lIPCoresModelsimIni, DEFAULT_ENCODING)
    for lSimLib in lSimLibs:
        cprint(f" - {lSimLib}")
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
def fli_eth(ictx, dev, ipbuspkg):
    """
    Build the Modelsim-ipbus foreign language interface
    """

    # -------------------------------------------------------------------------
    if ipbuspkg not in ictx.sources:
        raise click.ClickException(
            "Package %s not found in source/. The FLI cannot be built." % ipbuspkg
        )

    # Set ModelSim root based on vsim's path
    os.environ['MODELSIM_ROOT'] = dirname(dirname(which('vsim')))
    # Apply set
    # os.environ['MTI_VCO_MODE']='64'

    lFliSrc = join(
        ictx.srcdir,
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
def fli_udp(ictx, port, ipbuspkg):
    """
    Build the Modelsim-ipbus foreign language interface
    """

    # -------------------------------------------------------------------------
    if ipbuspkg not in ictx.sources:
        raise click.ClickException(
            "Package %s not found in source/. The FLI cannot be built." % ipbuspkg
        )

    # Set ModelSim root based on vsim's path
    os.environ['MODELSIM_ROOT'] = dirname(dirname(which('vsim')))
    # Apply set
    # os.environ['MTI_VCO_MODE']='64'

    lFliSrc = join(
        ictx.srcdir,
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
def genproject(ictx, aOptimise, aToScript, aToStdout):
    """
    Creates the modelsim project

    \b
    1. Compiles the source code into the 'work' simulation library. A different name can be specified with the `sim.library` dep file setting.
    2. Generates a 'run_sim' wrapper that sets the simulation environment before invoking vsim. The list of desing units to run can be specified with the `sim.run_sim.desing_units` dep file setting.

    NOTE: The ip/mac address of ipbus desings implementing a fli and exposing the ip/mac addresses via  top level generics can be set by defining the following user settings:

    \b
    - 'ipbus.fli.mac_address': mapped to MAC_ADDR top-level generic
    - 'ipbus.fli.ip_address': mapped to IP_ADDR top-level generic

    """

    # lSessionId = 'genproject'

    # -------------------------------------------------------------------------
    # Must be in a build area
    if ictx.currentproj.name is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again.'
        )

    if ictx.currentproj.settings['toolset'] != 'sim':
        raise click.ClickException(
            f"Project area toolset mismatch. Expected 'sim', found '{ictx.currentproj.settings['toolset']}'"
        )
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not which('vsim'):
        raise click.ClickException(
            'ModelSim (vsim) not found. Please add Modelsim to PATH and execute the command again.'
        )
    # -------------------------------------------------------------------------

    lDepFileParser = ictx.depParser

    lSimLibrary = lDepFileParser.settings.get(f'{_toolset}.library', 'work')

    # Ensure that no parsing errors are present
    ensureNoParsingErrors(ictx.currentproj.name, lDepFileParser)

    # Ensure that all dependencies are resolved
    ensureNoMissingFiles(ictx.currentproj.name, lDepFileParser)

    lSimProjMaker = ModelSimGenerator(ictx.currentproj, lSimLibrary, kIPVivadoProjName, aOptimise)

    lDryRun = aToStdout or aToScript

    if not lDryRun:
        sh.rm('-rf', lSimLibrary)

    try:
        with mentor.ModelSimBatch(aToScript, echo=aToStdout, dryrun=lDryRun) as lSim:
            lSimProjMaker.write(
                lSim,
                lDepFileParser.settings,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )
    except sh.ErrorReturnCode as e:
        console.log(
            f'ERROR: Sim exit code: {e.exit_code}.\nCommand:\n\n   {e.full_cmd}\n',
            style='red',
        )
        raise click.ClickException("Compilation failed")

    if lDryRun:
        return

    # ----------------------------------------------------------
    # Create a wrapper to force default bindings at load time
    cprint(f"Writing modelsim wrapper '{kVsimWrapper}'")

    lVsimArgStr = f"{lDepFileParser.settings.get(f'{_toolset}.{kVsimWrapper}.design_units', '')}"

    lVsimOpts = collections.OrderedDict()
    lVsimOpts['MAC_ADDR'] = validateMacAddress(
        ictx.currentproj.usersettings.get('ipbus.fli.mac_address', None)
    )
    lVsimOpts['IP_ADDR'] = validateIpAddress(
        ictx.currentproj.usersettings.get('ipbus.fli.ip_address', None)
    )

    lVsimOptStr = ' '.join(
        ['-G{}=\'{}\''.format(k, v) for k, v in lVsimOpts.items() if v is not None]
    )

    lVsimCmd = ' '.join(['vsim', lVsimArgStr, lVsimOptStr])

    lVsimBody = f'''#!/bin/sh

if [ ! -f modelsim.ini ]; then
    echo "WARNING: modelsim.ini not found. Vivado simulation libraries won't be loaded."
fi

export MTI_VCO_MODE=64
export MODELSIM_DATAPATH="mif/"
{lVsimCmd} "$@"
    '''
    with SmartOpen(kVsimWrapper) as lVsimSh:
        lVsimSh(lVsimBody)

    # Make it executable
    os.chmod(kVsimWrapper, 0o755)

    print(f"Vsim wrapper script '{kVsimWrapper}' created")
    if lVsimCmd:
        print(f"   Command: '{lVsimCmd}'")


# ------------------------------------------------------------------------------
def virtualtap(ictx, dev, ip):
    """Create a virtual tap device
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


# ------------------------------------------------------------------------------
def detect_ip_sim_srcs(projpath, projname, ipcores):

    lIPPaths = {}
    lIPProjDir = abspath(join(projpath, projname))
    for lGenDir in ['src', 'gen']:
        for lIP in ipcores:

            lIPPaths[lIP] = None
            for lSimDir in ['', 'sim']:
                # Hack required. The Vivado generated hdl files sometimes
                # have 'sim' in their path, sometimes don't
                p = abspath(
                    join(lIPProjDir, f'{projname}.{lGenDir}', 'sources_1', 'ip', lSimDir, lIP))

                if exists(p):
                    lIPPaths[lIP] = p
                    break

    return lIPPaths

# ------------------------------------------------------------------------------
def mifs(ictx):

    srcs = ictx.depParser.commands['src']

    # Seek mif files in sources
    lPaths = []
    for c in srcs:
        if splitext(c.filepath)[1] != '.mif':
            continue
        lPaths.append(c.filepath)

    # This is ancient....
    if lPaths:
        sh.mkdir('-p', 'mif')
        for p in lPaths:
            cprint(f"Copying {p} to the project area")
            sh.cp(p, 'mif/')

    lIPCores = [ f for f in find_ip_src(srcs)]

    lIPSrcs = { ip: find_ip_sim_src(ictx.currentproj.path, kIPVivadoProjName, ip, "dir") for ip in lIPCores}

    lMissingIPSimSrcs = [ k for k, v in lIPSrcs.items() if v is None]
    if lMissingIPSimSrcs:
        raise click.ClickException(f"Failed to collect mifs. Simulation sources not found for ip cores: {', '.join(lMissingIPSimSrcs)}")

    for c, d in lIPSrcs.items():
        for file in os.listdir(d):
            if file.endswith(".mif"):
                p = os.path.join(d, file)
                cprint(f"Copying {p} to the project area")
                sh.cp(p, '.')


