
# Modules
import click
import glob

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from ..console import cprint, console

from ..tools.common import which, SmartOpen
from ..utils import ensureNoParsingErrors, ensureNoMissingFiles, logVivadoConsoleError
from ..defaults import kTopEntity
from ..generators.vivadohlsproject import VivadoHlsProjectGenerator
from ..tools.xilinx import VivadoHLSSession, VivadoHLSConsoleError

_vivado_hls_group = 'vivado_hls'

# ------------------------------------------------------------------------------
def ensureVivadoHLS(ictx):
    if ictx.currentproj.settings['toolset'] != 'vivadohls':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivadohls', found '%s'"
            % ictx.currentproj.settings['toolset']
        )

    if not which('vivado_hls'):
        # if 'XILINX_VIVADO' not in os.ictxiron:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado ictxironment before continuing."
        )


# ------------------------------------------------------------------------------
def vivadohls(ictx, proj, verbosity):
    '''Vivado command group'''

    ictx.vivadoHlsEcho = (verbosity == 'all')

    if proj is not None:
        # Change directory before executing subcommand
        from .proj import cd

        cd(ictx, projname=proj, aVerbose=False)
        return
    else:
        if ictx.currentproj.name is None:
            raise click.ClickException(
                'Project area not defined. Move to a project area and try again'
            )

    ictx.vivado_hls_proj_path = join(ictx.currentproj.path, ictx.currentproj.name)
    ictx.vivado_hls_solution = ictx.depParser.settings.get(f'{_vivado_hls_group}.solution', 'sol1')
    

# ------------------------------------------------------------------------------
def genproject(ictx, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''

    lSessionId = 'generate-project'

    # Check if vivado is around
    ensureVivadoHLS(ictx)

    lDepFileParser = ictx.depParser

    # Ensure that no parsing errors are present
    ensureNoParsingErrors(ictx.currentproj.name, lDepFileParser)

    # Ensure that all dependencies are resolved
    ensureNoMissingFiles(ictx.currentproj.name, lDepFileParser)

    lVivadoMaker = VivadoHlsProjectGenerator(ictx.currentproj, ictx.vivado_hls_solution)

    lDryRun = aToScript or aToStdout
    lScriptPath = aToScript if not aToStdout else None

    try:
        with (
            VivadoHLSSession(sid=lSessionId, echo=ictx.vivadoHlsEcho) if not lDryRun
            else SmartOpen(lScriptPath)
        ) as lConsole:

            lVivadoMaker.write(
                lConsole,
                lDepFileParser.settings,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.rootdir,
            )

    except VivadoHLSConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        secho(
            "Error caught while generating Vivado TCL commands:\n" + "\n".join(lExc),
            fg='red',
        )
        raise click.Abort()
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def csynth(ictx):

    lSessionId = 'csynth'

    # Check if vivado is around
    ensureVivadoHLS(ictx)

    try:
        with VivadoHLSSession(sid=lSessionId, echo=ictx.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole(f'open_project {ictx.currentproj.name}')
            lConsole(f'open_solution {ictx.vivado_hls_solution}')
            lConsole('csynth_design')
# 

    except VivadoHLSConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log("ERROR:", style='red')
        console.print(lExc)
        raise click.Abort()

    console.log(f"{ictx.currentproj.name}: Synthesis completed successfully.", style='green')


# ------------------------------------------------------------------------------
def csim(ictx):

    lSessionId = 'sim'

    # Check if vivado is around
    ensureVivadoHLS(ictx)

    try:
        with VivadoHLSSession(sid=lSessionId, echo=ictx.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole(f'open_project {ictx.currentproj.name}')
            lConsole(f'open_solution {ictx.vivado_hls_solution}')
            lConsole('csim_design')
# 

    except VivadoHLSConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log("ERROR:", style='red')
        console.print(lExc)
        raise click.Abort()

    console.log(f"{ictx.currentproj.name}: Simulation completed successfully.", style='green')


# ------------------------------------------------------------------------------
def cosim(ictx):
    lSessionId = 'cosim'

    # Check if vivado is around
    ensureVivadoHLS(ictx)

    try:
        with VivadoHLSSession(sid=lSessionId, echo=ictx.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole(f'open_project {ictx.currentproj.name}')
            lConsole(f'open_solution {ictx.vivado_hls_solution}')
            lConsole('cosim_design')
# 

    except VivadoHLSConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log("ERROR:", style='red')
        console.print(lExc)
        raise click.Abort()

    console.log(f"{ictx.currentproj.name}: Cosimulation completed successfully.", style='green')


# ------------------------------------------------------------------------------
def export_ip_catalog(ictx):
    from ..defaults import kTopEntity

    lSessionId = 'export-ip-catalog'
    
    console.log('I shall run export_design -flow syn -rtl vhdl -format ip_catalog -description "A description" -vendor "me" -library "mylib" -version "1.2.3" -display_name "hello"')
    console.log('which should generate "hls_example/sol1/impl/ip/me_mylib_add7_1_2.zip"')

    """
    zipfile name = "<vendor>_<lib>_<top>_<versionmajor>_<versionminor>.zip"
    defaults: 
    - vendor = "xilinx.com" -> "xilinx_com"
    - lib = "hls"
    - version = "1.0"
    - ipname = "top_entity"
    """

    reqsettings = {'vendor', 'library', 'version'}

    lSettings = ictx.depParser.settings
    lHLSSettings = lSettings.get(_vivado_hls_group, {})

    cprint(reqsettings)
    print(reqsettings.difference(lHLSSettings))
    if not lHLSSettings or not reqsettings.issubset(lHLSSettings):
        raise RuntimeError(f"Missing variables required to create an ip repository: {', '.join([f'{_vivado_hls_group}.{s}' for s in reqsettings.difference(lHLSSettings)])}")

    lIPName = lHLSSettings['ipname'] if 'ipname' in lHLSSettings else lSettings.get('top_entity', kTopEntity)
    lIPVendor = lHLSSettings['vendor']
    lIPLib = lHLSSettings['library']
    lIPVersion = lHLSSettings['version']
    lIpRepoName = f"{lIPVendor.replace('.', '_')}_{lIPLib.replace('.', '_')}_{lIPName}_{lIPVersion.replace('.', '_')}"
    # Check if vivado is around
    ensureVivadoHLS(ictx)

    try:
        with VivadoHLSSession(sid=lSessionId, echo=ictx.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole(f'open_project {ictx.currentproj.name}')
            lConsole(f'open_solution {ictx.vivado_hls_solution}')
            lConsole(f'export_design -flow syn -format ip_catalog -ipname {lIPName} -vendor {lHLSSettings["vendor"]} -library {lHLSSettings["library"]} -version "{lHLSSettings["version"]}"')

    except VivadoHLSConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log("ERROR:", style='red')
        console.print(lExc)
        raise click.Abort()

    console.log(f"{ictx.currentproj.name}: Export completed successfully.", style='green')

    lIPCatalogDir = join(ictx.currentproj.name, ictx.vivado_hls_solution, 'impl', 'ip')
    zips = glob.glob(join(lIPCatalogDir, "*.zip"))

    if len(zips) == 0:
        raise RuntimeError(f"IP catalog file not found in {lIPCatalogDir}")
    elif len(zips) > 1:
        raise RuntimeError(f"Multiple IP catalog file not found in {lIPCatalogDir}: {zips}")
    lIPCatalogPath = zips.pop()

    console.log(f"{ictx.currentproj.name}: HLS ips catalog exported to {lIPCatalogPath}", style='green')


def debug(ictx):
    console.log(ictx.vivado_hls_solution)
    pass
