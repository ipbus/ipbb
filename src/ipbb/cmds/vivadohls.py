
# Modules
import click
import glob
import shutil
import cerberus

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from ..console import cprint, console

from ..tools.common import which, SmartOpen, mkdir
from ..utils import ensureNoParsingErrors, ensureNoMissingFiles, logVivadoConsoleError
from ..defaults import kTopEntity
from ..generators.vivadohlsproject import VivadoHlsProjectGenerator
from ..tools.xilinx import VivadoHLSSession, VivadoHLSConsoleError, VivadoSession, VivadoConsoleError


# @device_generation = "UltraScalePlus"
# @device_name = "xcku15p"
# @device_package = "-ffva1760"
# @device_speed = "-2-e"
# @boardname = "serenity-dc-ku15p"

# @top_entity = "add7"
# @vivado_hls.solution = "mysol"
# @vivado_hls.vendor = "cern_cms"
# @vivado_hls.library = "emp_hls_examples"
# @vivado_hls.version = "1.1"
_vivado_hls_group='vivado_hls'
_schema = {
    'device_generation': {'type': 'string'},
    'device_name': {'type': 'string'},
    'device_speed': {'type': 'string'},
    'boardname': {'type': 'string'},
    'top_entity': {'type': 'string'},
    'vivado_hls': {
        'schema': {
            'solution': {'type': 'string'},
            'ipname': {'type': 'string'},
            'vendor': {'type': 'string'},
            'library': {'type': 'string'},
            'version': {'type': 'string', 'regex': r'\d\.\d(\.\d)?'},
        }
    }

}

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
    ictx.vivado_hls_prod_path = join(ictx.currentproj.path, 'ip')
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
def export_ip(ictx, to_component):
    """
    TODO : allow user to choose what export_desing flow to use
    """
    from ..defaults import kTopEntity

    lSessionId = 'export-ip-catalog'
    
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

    if not lHLSSettings or not reqsettings.issubset(lHLSSettings):
        raise RuntimeError(f"Missing variables required to create an ip repository: {', '.join([f'{_vivado_hls_group}.{s}' for s in reqsettings.difference(lHLSSettings)])}")

    lIPName = lHLSSettings['ipname'] if 'ipname' in lHLSSettings else lSettings.get('top_entity', kTopEntity)
    lIPVendor = lHLSSettings['vendor']
    lIPLib = lHLSSettings['library']
    lIPVersion = lHLSSettings['version']
    lIpRepoName = f"{lIPVendor.replace('.', '_')}_{lIPLib.replace('.', '_')}_{lIPName}_{lIPVersion.replace('.', '_')}"

    # Check if vivado_hls is accessible
    ensureVivadoHLS(ictx)

    # -- Export the HSL code as a Xilinx IP catalog
    console.log("Exporting IP catalog")
    try:
        with VivadoHLSSession(sid=lSessionId, echo=ictx.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole(f'open_project {ictx.currentproj.name}')
            lConsole(f'open_solution {ictx.vivado_hls_solution}')
            lConsole(f'export_design -format ip_catalog -ipname {lIPName} -vendor {lHLSSettings["vendor"]} -library {lHLSSettings["library"]} -version "{lHLSSettings["version"]}"')

    except VivadoHLSConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log("ERROR:", style='red')
        console.print(lExc)
        raise click.Abort()


    lIPCatalogDir = join(ictx.currentproj.name, ictx.vivado_hls_solution, 'impl', 'ip')
    zips = glob.glob(join(lIPCatalogDir, "*.zip"))

    if len(zips) == 0:
        raise RuntimeError(f"IP catalog file not found in {lIPCatalogDir}")
    elif len(zips) > 1:
        raise RuntimeError(f"Multiple IP catalog file found in {lIPCatalogDir}: {zips}")
    lIPCatalogExportPath = zips.pop()
    lIPCatalogName = basename(lIPCatalogExportPath)
    lIPCatalogRoot, _ = splitext(lIPCatalogName)
    lIPCatalogZip = join(ictx.vivado_hls_prod_path, lIPCatalogName)
    lXciModName = f"{lIPLib}_{lIPName}"

    # -- Generate an XCI file for the IP
    mkdir(ictx.vivado_hls_prod_path)
    shutil.copy(lIPCatalogExportPath, lIPCatalogZip)

    console.log(f"{ictx.currentproj.name}: HLS IP catalog exported to {lIPCatalogZip}", style='green')
    console.log("Creating XCI file")

    lXilinxPart = f'{lSettings["device_name"]}{lSettings["device_package"]}{lSettings["device_speed"]}'

    try:
        with VivadoSession(sid=lSessionId) as lVivadoConsole:
            lVivadoConsole(f'create_project -in_memory -part {lXilinxPart} -force')
            lVivadoConsole(f'set_property ip_repo_paths {lIPCatalogDir} [current_project]')
            lVivadoConsole('update_ip_catalog -rebuild')
            lVivadoConsole('set repo_path [get_property ip_repo_paths [current_project]]')
            ip_vlnv_list = lVivadoConsole(f'foreach n [get_ipdefs -filter REPOSITORY==$repo_path] {{ puts "$n" }}')
            if len(ip_vlnv_list) > 1:
                raise RuntimeError(f"Found more than 1 core in ip catalog! {', '.join(ip_vlnv_list)}")
            vlnv = ip_vlnv_list[0]
            lVivadoConsole(f'create_ip -vlnv {vlnv} -module_name {lXciModName} -dir {ictx.vivado_hls_prod_path}')

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log("ERROR:", style='red')
        console.print(lExc)
        raise click.Abort()

    dest = to_component if to_component is not None else (ictx.currentproj.settings['topPkg'], ictx.currentproj.settings['topCmp'])

    lIPDest = ictx.pathMaker.getPath(*dest, 'iprepo')
    lIPRepoDest = join(lIPDest, lIPCatalogRoot)

    shutil.rmtree(lIPRepoDest, True)
    mkdir(lIPRepoDest)
    from zipfile import ZipFile

    with ZipFile(lIPCatalogZip, 'r') as zipObj:
        zipObj.extractall(lIPRepoDest)
    console.log(f"{lIPCatalogName} unzipped into {lIPRepoDest}")

    shutil.copy(join(ictx.vivado_hls_prod_path, lXciModName, f'{lXciModName}.xci'), lIPDest)
    console.log(f"{lXciModName}.xci copied to {lIPDest}")
    console.log(f"{ictx.currentproj.name}: Export completed successfully.", style='green')



# ------------------------------------------------------------------------------
def debug(ictx):

    v = cerberus.Validator(_schema)
    lSettings = ictx.depParser.settings
    lHLSSettings = lSettings.get(_vivado_hls_group, {})
    # Need to convert the settings to a plain dict
    # Need to add a walk-like iterator
    # v.validate(lHLSSettings)


    pass
