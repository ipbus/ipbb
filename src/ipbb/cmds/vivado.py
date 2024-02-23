
# Modules
import click
import os
import sys
import sh
import time
import types
import socket
import yaml
import re
import cerberus

# Elements
from os.path import join, split, exists, splitext, abspath, basename, getmtime
from collections import OrderedDict
from copy import deepcopy
from rich.table import Table

from .schema import project_schema, validate_schema
from .dep import hash

from ..console import cprint, console
from ..utils import which, SmartOpen, mkdir
from ..utils import ensureNoParsingErrors, ensureNoMissingFiles, logVivadoConsoleError, warning_notice

from ..generators.vivadoproject import VivadoProjectGenerator
from ..tools.xilinx import VivadoSession, VivadoSessionManager, VivadoConsoleError, VivadoSnoozer, VivadoProject
from ..defaults import kTopEntity


_toolset='vivado'
_schema = deepcopy(project_schema)
_schema.update({
    _toolset: {
        'schema': {
            'binfile_options': {'type': 'string'},
            'mcsfile_options': {'type': 'string'},
        }
    }
})

_memCfgKinds = {
    'bin': 'binfile_options',
    'mcs': 'mcsfile_options'
}

_svfSettingName = 'svf_jtagchain_devices'


_rum_synth = 'synth_1'
_rum_impl = 'impl_1'



# ------------------------------------------------------------------------------
def validate_settings(ictx):

    validate_schema(_schema, ictx.depParser.settings)



# ------------------------------------------------------------------------------
def ensure_vivado(ictx):
    """Utility function guaranteeing the correct Vivado environment.
    
    Args:
        ictx (ipbb.Context): Context object
    
    Raises:
        click.ClickException: Toolset mismatch or Vivado not available
    """
    if ictx.currentproj.settings['toolset'] != _toolset:
        raise click.ClickException(
            f"Work area toolset mismatch. Expected {_toolset}, found '{ictx.currentproj.settings['toolset']}'"
        )

    if not which('vivado'):
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing."
        )

# ------------------------------------------------------------------------------
def ensure_vivado_project_path(aProjPath: str):
    """Utility function to ensure that the project path exists
    
    Args:
        aProjPath (str): Vivado Project path
    
    Raises:
        click.ClickException: Description
    """
    if not exists(aProjPath):
        raise click.ClickException("Vivado project %s does not exist" % aProjPath)

# ------------------------------------------------------------------------------
def vivado(ictx, loglevel, cmdlist):
    '''Vivado command group
    
    Args:
        ctx (click.Context): Command context
        ictx (ipbb.Context): Context object
        proj (str): Project name
        loglevel (str): Verbosity level
    
    Raises:
        click.ClickException: Undefined project area
    '''


    # if proj is not None:
    #     # Change directory before executing subcommand
    #     from .proj import cd

    #     cd(ictx, projname=proj, aVerbose=False)

    if ictx.currentproj.name is None:
        raise click.ClickException(
            'Project area not defined. Move to a project area and try again'
        )
    
    validate_settings(ictx)

    lKeep = True
    lLogLabel = None if not lKeep else '_'.join( cmdlist )

    # Command-specific ictx variables
    ictx.vivadoProjPath = join(ictx.currentproj.path, ictx.currentproj.name)
    ictx.vivadoProjFile = join(ictx.vivadoProjPath, ictx.currentproj.name +'.xpr')
    ictx.vivadoProdPath = join(ictx.currentproj.path, 'products')
    ictx.vivadoProdFileBase = join(ictx.vivadoProdPath, ictx.currentproj.name)
    ictx.vivado_synth_dir = join(ictx.vivadoProjPath, f'{ictx.currentproj.name}', _rum_synth)
    ictx.vivado_impl_dir = join(ictx.vivadoProjPath, f'{ictx.currentproj.name}.runs', _rum_impl)

    ictx.vivadoSessions = VivadoSessionManager(keep=lKeep, echo=(loglevel != 'none'), loglabel=lLogLabel, loglevel=loglevel)

    ensure_vivado(ictx)



# ------------------------------------------------------------------------------
def genproject(ictx, aEnableIPCache, aOptimise, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''

    lSessionId = 'generate-project'

    # Check if vivado is around
    ensure_vivado(ictx)

    lDepFileParser = ictx.depParser

    # Ensure that no parsing errors are present
    ensureNoParsingErrors(ictx.currentproj.name, lDepFileParser)

    # Ensure that all dependencies are resolved
    ensureNoMissingFiles(ictx.currentproj.name, lDepFileParser)

    lVivadoIPCache = join(ictx.work.path, 'var', 'vivado-ip-cache') if aEnableIPCache else None
    lVivadoGen = VivadoProjectGenerator(ictx.currentproj, lVivadoIPCache, aOptimise)

    if aToScript or aToStdout:
        # Dry run
        lConsoleCtx = SmartOpen(aToScript if not aToStdout else None)
    else:
        lConsoleCtx = ictx.vivadoSessions.getctx(lSessionId)

    try:
        with lConsoleCtx as lConsole:
            lVivadoGen.write(
                lConsole,
                lDepFileParser.settings,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        cprint(
            "Error caught while generating Vivado TCL commands:",
            style='red'
        )
        cprint(lExc)
        raise click.Abort()
    
    console.log(
        f"{ictx.currentproj.name}: Project created successfully.",
        style='green',
    )
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def checksyntax(ictx):

    lSessionId = 'chk-syn'

    lStopOn = ['HDL 9-806', 'HDL 9-69', 'HDL 9-3136', 'HDL 9-1752' ]  # Syntax errors  # Type not declared # object not declared # found 0 definitions of operator...

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            # Open the project
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)

            # Change message severity to ERROR for the isses we're interested in
            lConsole.changeMsgSeverity(lStopOn, 'ERROR')

            # Execute the syntax check
            lConsole('check_syntax')

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    console.log(
        "\n{}: Syntax check completed successfully.\n".format(ictx.currentproj.name),
        style='green',
    )

# -------------------------------------
def synth(ictx, aNumJobs, aUpdateInt):
    '''Run synthesis'''

    lSessionId = 'synth'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    lArgs = []

    if aNumJobs is not None:
        lArgs += ['-jobs {}'.format(aNumJobs)]

    lOOCRegex = re.compile(r'.*_synth_\d+')
    lSynthRun = 'synth_1'

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            # Open the project
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)

            with VivadoSnoozer(lConsole):
                lRunProps = { k: v for k, v in read_run_info(lConsole).items() if lOOCRegex.match(k) }

            # Reset all OOC synthesis which might are stuck in a running state
            lIPRunsToReset = [
                k for k, v in lRunProps.items()
                if v['STATUS'].startswith('Running')
            ]

            # Reset IP runs, if needed
            for run in lIPRunsToReset:
                cprint(
                    f"IP run {run} found in running state. Resetting.",
                    style='yellow',
                )
                lConsole(f'reset_run {run}')

            # Reset and launch synth_1
            lConsole(f'reset_run {lSynthRun}')
            lConsole(f'launch_runs {lSynthRun} {" ".join(lArgs)}')

            # Monitor OOC and synth run progress
            if not aUpdateInt:
                cprint("Run monitoring disabled", style='cyan')
                lConsole('wait_on_run synth_1')
            else:
                cprint(f"Starting run monitoring loop, update interval: {aUpdateInt} min(s)", style='cyan')
                while True:

                    with VivadoSnoozer(lConsole):
                        lRunProps = read_run_info(lConsole)

                    lOOCRunProps = { k: v for k, v in lRunProps.items() if lOOCRegex.match(k) }
                    # Reset all OOC synthesis which might are stuck in a running state
                    lPendingOOCRuns = [
                        k for k, v in lOOCRunProps.items()
                        if ( not v['STATUS'].startswith('synth_design Complete!') and not v['STATUS'].startswith('Not started') )
                    ]

                    if lPendingOOCRuns:
                        cprint(make_runs_table(lOOCRunProps), style='light_sky_blue1')
                    else:
                        cprint(f"OOC runs: {len(lOOCRunProps)} completed.", style='light_sky_blue1')

                    lSynthProps = { k: v for k, v in lRunProps.items() if k == lSynthRun }

                    cprint(make_runs_table(lSynthProps), style='light_sky_blue1')

                    lRunsInError = [ k for k, v in lRunProps.items() if v['STATUS'] == 'synth_design ERROR']
                    if lRunsInError:
                        raise RuntimeError(f"Detected runs in ERROR {', '.join(lRunsInError)}. Exiting")

                    # Synthesis finished, get out of there
                    if lRunProps['synth_1']['PROGRESS'] == '100%':
                        break

                    lConsole(f'wait_on_run synth_1 -timeout {aUpdateInt}')

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        console.log(
            "ERROR",
            style='red',
        )
        console.log(lExc)
        raise click.Abort()

    console.log(
        f"{ictx.currentproj.name}: Synthesis completed successfully.",
        style='green',
    )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def impl(ictx, aNumJobs, aStopOnTimingErr):
    '''
    Launch an implementation run
    '''

 
    lSessionId = 'impl'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    lStopOn = []
    if aStopOnTimingErr:
        # List of vivado message that are expected to result into an error.
        lStopOn = ['Timing 38-282']  # Force error when timing is not met

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:

            # Open the project
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)

            # Change message severity to ERROR for the isses we're interested in
            lConsole.changeMsgSeverity(lStopOn, "ERROR")

            for c in (
                    f'reset_run {_rum_impl}',
                    f'launch_runs {_rum_impl}'
                    + (' -jobs {}'.format(aNumJobs) if aNumJobs is not None else ''),
                    f'wait_on_run {_rum_impl}',
                ):
                lConsole(c)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    console.log(
        f"{ictx.currentproj.name}: Implementation completed successfully.\n",
        style='green',
    )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------

def resource_usage(ictx, aCell, aDepth, aFile, aSLR):

    lSessionId = 'usage'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    lCmd = 'report_utilization '
    if aSLR:
        lCmd += ' -slr '
    else:
        lCmd += ' -hierarchical -hierarchical_depth {} -hierarchical_percentages'.format(aDepth)
    if aCell:
        lCmd += ' -cells ' + aCell

    if aFile:
        lCmd += ' -file ' + aFile


    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
            for c in (
                    'open_run impl_1',
                    lCmd
                ):
                lConsole(c)
    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()


# ------------------------------------------------------------------------------
def bitfile(ictx):
    '''Create a bitfile'''

    lSessionId = 'bitfile'

    # Check
    if not exists(ictx.vivadoProjFile):
        raise click.ClickException("Vivado project %s does not exist" % ictx.vivadoProjFile)

    ensure_vivado(ictx)

    mkdir(ictx.vivadoProdPath)
    lWriteBitStreamCmd = 'write_bitstream -force {}'.format(ictx.vivadoProdFileBase+'.bit')


    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
            lProject.open_run('impl_1')
            lConsole(lWriteBitStreamCmd)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    console.log(
        f"{ictx.currentproj.name}: Bitfile successfully written.",
        style='green'
    )


# ------------------------------------------------------------------------------
def _svffile(ictx):
    '''Create a Serial Vector Format (SVF) file
    
    Requires the JTAG chain to be specific in the depfile: vivado.svf_jtagchain_devices
    '''
    lSessionId = 'svffile'

    # Check that the project exists
    ensure_vivado_project_path(ictx.vivadoProjFile)

    lProjName = ictx.currentproj.name
    lDepFileParser = ictx.depParser
    lBaseName = ictx.vivadoProdFileBase

    # Return early if SVF settings not found
    if ('vivado' not in lDepFileParser.settings) or _svfSettingName not in lDepFileParser.settings['vivado']:
        cprint('No SVF settings found in this project. Exiting.', style='yellow')
        return

    lDevicesBefore = lDepFileParser.settings['vivado'][_svfSettingName][0]
    lDevicesAfter = lDepFileParser.settings['vivado'][_svfSettingName][1]

    lBitPath = lBaseName + '.bit'
    if not exists(lBitPath):
        raise click.ClickException("Bitfile does not exist. Can't create SVF file.")

    # Check that that the Vivado ictx is up
    ensure_vivado(ictx)

    # First few TCL commands: Open HW server and create an SVF target
    lTclCommands = [
        'open_hw',
        'connect_hw_server',
        'delete_hw_target -quiet [get_hw_devices -quiet */ipbb_svf_target]',
        'create_hw_target ipbb_svf_target',
        'open_hw_target [get_hw_targets */ipbb_svf_target]'
    ]

    # 2nd set of TCL commands: Declare the JTAG chain
    for x in lDevicesBefore:
        lTclCommands.append('create_hw_device ' + x)

    lXilinxPart = f'{lDepFileParser.settings["device_name"]}{lDepFileParser.settings["device_package"]}{lDepFileParser.settings["device_speed"]}'
    lTclCommands.append(f'set DEVICE [create_hw_device -part {lXilinxPart}]')

    for x in lDevicesAfter:
        lTclCommands.append('create_hw_device ' + x)

    # Last set of TCL commands: Convert the bitstream to the SVF file (by programming the dummy SVF target)
    lSVFPath = lBaseName + '.svf'
    lTclCommands += [
        f'set_property PROGRAM.FILE {lBitPath} $DEVICE',
        'set_param xicom.config_chunk_size 0',
        #'set_property BITSTREAM.GENERAL.COMPRESS TRUE [current_design]',
        f'program_hw_devices $DEVICE',
        f'write_hw_svf {lSVFPath}',
        'close_hw_target'
    ]

    # Execute the TCL commands
    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:

            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
            for c in lTclCommands:
                lConsole(c)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    console.log(
        f"{ictx.currentproj.name}: SVF file successfully written.",
        style='green'
    )


# ------------------------------------------------------------------------------
def debugprobes(ictx):
    '''Generate (optional) debug-probes files (used for ILAs and VIO controls).'''

    lSessionId = 'dbg-prb'

    # Check that the project exists.
    ensure_vivado_project_path(ictx.vivadoProjFile)

    lProjName = ictx.currentproj.name
    lDepFileParser = ictx.depParser
    lBaseName = ictx.vivadoProdFileBase

    lBitPath = lBaseName + '.bit'
    if not exists(lBitPath):
        raise click.ClickException("Bitfile does not exist. Can't create debug-probes files.")

    # And that the Vivado ictx is up.
    ensure_vivado(ictx)

    lWriteDebugProbesCmd = 'write_debug_probes -force {}'.format(ictx.vivadoProdFileBase+'.ltx')

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
            lProject.open_run('impl_1')
            lConsole(lWriteDebugProbesCmd)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    console.log(
        f"{ictx.currentproj.name}: Debug probes file successfully written.",
        style='green'
    )


# ------------------------------------------------------------------------------
def memcfg(ictx):
    '''Create a memcfg file for PROM programming
    
    Supports bin and mcs file types
    Requires the corresponding options to be defined in the dep files:
 
    * bin: 'vivado.binfile_options',
    * mcs: 'vivado.mcsfile_options'
    '''

    lSessionId = 'memcfg'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)



    lProjName = ictx.currentproj.name
    lDepFileParser = ictx.depParser
    lBaseName = ictx.vivadoProdFileBase

    if 'vivado' not in lDepFileParser.settings:
        cprint('No memcfg settings found in this project. Exiting.', style='yellow')
        return

    lBitPath = lBaseName + '.bit'
    if not exists(lBitPath):
        raise click.ClickException("Bitfile does not exist. Can't create memcfg files.")

    # And that the Vivado ictx is up
    ensure_vivado(ictx)
    
    lVivadoCfg = lDepFileParser.settings['vivado']
    for k,o in _memCfgKinds.items():

        if o not in lVivadoCfg:
            cprint(f"No configuration found for '{k}' files. Skipping.")
            continue

        lMemCmdOptions = lVivadoCfg[o]
        lMemPath = lBaseName+'.'+k

        try:
            with ictx.vivadoSessions.getctx(lSessionId) as lConsole:

                lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
                lConsole(
                    f'write_cfgmem -force -format {k} {lMemCmdOptions} -loadbit {{up 0x00000000 "{lBitPath}" }} -file "{lMemPath}"'
                )
        except VivadoConsoleError as lExc:
            logVivadoConsoleError(lExc)
            raise click.Abort()

        console.log(
            f"{ictx.currentproj.name}: {k.capitalize()} file successfully written.",
            style='green'
        )

# ------------------------------------------------------------------------------
def read_run_info(aConsole, aProps=None):
    lInfos = {}
    lProps = aProps if aProps is not None else [
        'STATUS',
        'NEEDS_REFRESH',
        'PROGRESS',
        # 'IS_IMPLEMENTATION',
        # 'IS_SYNTHESIS',
        'STATS.ELAPSED',
        # 'STATS.ELAPSED',
    ]

    # Gather data about existing runs
    lRuns = aConsole('get_runs')[0].split()

    for lRun in sorted(lRuns):

        lValues = (
                aConsole('get_property {0} [get_runs {1}]'.format(p, lRun))[0]
                for p in lProps
            )
        lInfos[lRun] = OrderedDict(zip(lProps, lValues))

    return lInfos

# ------------------------------------------------------------------------------
def make_runs_table(aInfos, title=None):
    lSummary = Table("Run", *list(next(iter(aInfos.values()))), title=title)
    if not aInfos:
        return lSummary

    for lRun in sorted(aInfos):
        lInfo = aInfos[lRun]
        lSummary.add_row(lRun, *list(lInfo.values()))
    return lSummary

# ------------------------------------------------------------------------------
def status(ictx):
    '''Show the status of all runs in the current project.'''

    lSessionId = 'status'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    lInfos = {}
    lProps = [
        'STATUS',
        'NEEDS_REFRESH',
        'PROGRESS',
        # 'IS_IMPLEMENTATION',
        # 'IS_SYNTHESIS',
        'STATS.ELAPSED',
    ]

    lOOCRegex = re.compile(r'.*_synth_\d+')
    lRunRegex = re.compile(r'(synth|impl)_\d+')

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            with VivadoSnoozer(lConsole):
                lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
                lInfos = lProject.read_run_info(lProps)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    lOocTable = make_runs_table({ k: v for k, v in lInfos.items() if lOOCRegex.match(k)}, title="Out of context runs")
    cprint(lOocTable)
    lDesignRuns = make_runs_table({ k: v for k, v in lInfos.items() if lRunRegex.match(k)}, title="Design runs")
    cprint(lDesignRuns)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def reset(ictx):
    '''Reset synth and impl runs'''

    lSessionId = 'reset'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
            for c in (
                    'reset_run synth_1',
                    'reset_run impl_1'
                ):
                lConsole(c)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    console.log(
        f"{ictx.currentproj.name}: synth_1 and impl_1 successfully reset.",
        style='green',
    )
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def package(ictx, aTag):
    '''
    Package bitfile with address table and file list
        Generate the bitfile if it doesn't exist
    '''

    def get_max_mtime_in_dir(path):
        root, _, files = next(iter( os.walk(path)))

        # from datetime import datetime
        # for f in files:
        #     cprint(f"{join(root, f)} {datetime.fromtimestamp(getmtime(join(root, f)))}")
        return max(os.path.getmtime(join(root, f)) for f in files)

    ensure_vivado(ictx)

    if not exists(ictx.vivadoProjFile):
        cprint('Vivado project does not exist. Creating the project...', style='yellow')
        genproject(ictx, True, True, None, False)

    lProjName = ictx.currentproj.name
    lDepFileParser = ictx.depParser
    lTopEntity = lDepFileParser.settings.get('top_entity', kTopEntity)

    # Create bitfile if missing
    lBaseName = ictx.vivadoProdFileBase
    lBitPath  = lBaseName + '.bit'
    gen_bitfile = False
    if not exists(lBitPath):
        cprint("Bitfile does not exist. Starting a build ...", style='yellow')
        gen_bitfile = True
    elif get_max_mtime_in_dir(ictx.vivado_impl_dir) > getmtime(lBitPath):
        cprint(f"Bitfile exists but it's older than the content of {_rum_impl}. Rebuilding ...", style='yellow')
        gen_bitfile = True

    if gen_bitfile:
        bitfile(ictx)

    # Create SVF file if requested
    lSVFPath = None
    try:
        lVivadoCfg = lDepFileParser.settings['vivado']
        if _svfSettingName in lVivadoCfg:
            lSVFPath = lBaseName + '.svf'
            if not exists(lSVFPath):
                _svffile(ictx)
    except KeyError as e:
        lSVFPath = None

    # Create configuration memory files if requested and missing
    try:
        lVivadoCfg = lDepFileParser.settings['vivado']
        lActiveMemCfgs = [k for k,o in _memCfgKinds.items() if o in lVivadoCfg]
        lMemCfgFiles = [lBaseName + '.' + k for k in lActiveMemCfgs]

        if any([not exists(f) for f in lMemCfgFiles]):
            memcfg(ictx)
    except KeyError as e:
        lMemCfgFiles = []

    lDebugProbesPath = lBaseName + '.ltx'
    if not os.path.exists(lDebugProbesPath):
        lDebugProbesPath = None

    lPkgPath = 'package'
    lPkgSrcPath = join(lPkgPath, 'src')

    # Cleanup first
    sh.rm('-rf', lPkgPath, _out=sys.stdout)

    # Create the folders
    try:
        os.makedirs(join(lPkgSrcPath, 'addrtab'))
    except OSError:
        pass

    # -------------------------------------------------------------------------
    # Generate a json signature file

    console.log("Generating summary files", style='blue')

    # -------------------------------------------------------------------------

    lHash = hash(ictx, output=join(lPkgSrcPath, 'hashes.txt'), verbose=True)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    lSummary = dict(ictx.currentproj.settings)
    lSummary.update(
        {
            'build host': socket.gethostname().replace('.', '_'),
            'time': time.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'md5': lHash.hexdigest(),
        }
    )

    with open(join(lPkgSrcPath, 'summary.txt'), 'w') as lSummaryFile:
        yaml.safe_dump(lSummary, lSummaryFile, indent=2, default_flow_style=False)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Copy bitfile, memcfg, and address table into the packaging area
    console.log("Collecting bitfile", style='blue')
    sh.cp('-av', lBitPath, lPkgSrcPath, _out=sys.stdout)

    if lSVFPath is not None:
        console.log("Collecting SVF file {}".format(lSVFPath), style='blue')
        sh.cp('-av', lSVFPath, lPkgSrcPath, _out=sys.stdout)

    for f in lMemCfgFiles:
        console.log("Collecting memcfg {}".format(f), style='blue')
        sh.cp('-av', f, lPkgSrcPath, _out=sys.stdout)

    if lDebugProbesPath:
        console.log("Collecting debug-probes file", style='blue')
        sh.cp('-av', lDebugProbesPath, lPkgSrcPath, _out=sys.stdout)

    console.log("Collecting address tables", style='blue')
    for addrtab in ictx.depParser.commands['addrtab']:
        sh.cp('-avL', addrtab.filepath, join(lPkgSrcPath, 'addrtab'), _out=sys.stdout)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Tar everything up
    console.log("Creating tarball", style='blue')

    lTgzBaseName = '_'.join(
        [ictx.currentproj.settings['name']]
        + ([aTag] if aTag is not None else [])
        + [socket.gethostname().replace('.', '_'), time.strftime('%y%m%d_%H%M')]
    )
    lTgzPath = join(lPkgPath, lTgzBaseName + '.tgz')

    # Zip everything
    sh.tar(
        'cvfz',
        abspath(lTgzPath),
        '-C',
        lPkgPath,
        '--transform',
        's|^src|' + lTgzBaseName + '|',
        'src',
        _out=sys.stdout,
    )

    console.log(
        f"Package {lTgzPath} successfully created.",
        style='green',
    )
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def archive(ictx):

    lSessionId = 'archive'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    try:
        with ictx.vivadoSessions.getctx(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
            lConsole('archive_project {} -force'.format(
                    join(ictx.currentproj.path, ictx.currentproj.settings['name']+'.xpr.zip')
                )
            )
    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()


# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def ipy(ictx):

    lSessionId = 'ipy'

    # Check that the project exists 
    ensure_vivado_project_path(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensure_vivado(ictx)

    lConsole = ictx.vivadoSessions._getconsole(lSessionId)
    lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
    import IPython

    IPython.embed(colors="neutral")
