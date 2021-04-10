
# Modules
import click
import os
import ipbb
import sys
import sh
import time
import types
import socket
import yaml
import re

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from collections import OrderedDict
from copy import deepcopy
from rich.table import Table

from .schema import project_schema
from .dep import hash

from ..console import cprint, console
from ..tools.common import which, SmartOpen, mkdir
from ..utils import ensureNoParsingErrors, ensureNoMissingFiles, logVivadoConsoleError

from ..generators.vivadoproject import VivadoProjectGenerator
from ..tools.xilinx import VivadoSession, VivadoSessionManager, VivadoConsoleError, VivadoSnoozer, VivadoProject
from ..defaults import kTopEntity


_vivado_group='vivado'
_schema = deepcopy(project_schema)
_schema.update({
    _vivado_group: {
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

# ------------------------------------------------------------------------------
def ensureVivado(ictx):
    """Utility function guaranteeing the correct Vivado environment.
    
    Args:
        ictx (ipbb.Context): Context object
    
    Raises:
        click.ClickException: Toolset mismatch or Vivado not available
    """
    if ictx.currentproj.settings['toolset'] != 'vivado':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivado', found '%s'"
            % ictx.currentproj.settings['toolset']
        )

    if not which('vivado'):
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing."
        )

# ------------------------------------------------------------------------------
def ensureVivadoProjPath(aProjPath):
    """Utility function to ensure that the project path exists
    
    Args:
        aProjPath (TYPE): Description
    
    Raises:
        click.ClickException: Description
    """
    if not exists(aProjPath):
        raise click.ClickException("Vivado project %s does not exist" % aProjPath)

# ------------------------------------------------------------------------------
def vivado(ictx, proj, verbosity, cmdlist):
    '''Vivado command group
    
    Args:
        ctx (click.Context): Command context
        ictx (ipbb.Context): Context object
        proj (str): Project name
        verbosity (str): Verbosity level
    
    Raises:
        click.ClickException: Undefined project area
    '''

    ictx.vivadoEcho = (verbosity == 'all')

    # lProj = proj if proj is not None else ictx.currentproj.name
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

    ensureVivado(ictx)

    lKeep = True
    lLogLabel = None if not lKeep else '_'.join( cmdlist )

    # Command-specific ictx variables
    ictx.vivadoProjPath = join(ictx.currentproj.path, ictx.currentproj.name)
    ictx.vivadoProjFile = join(ictx.vivadoProjPath, ictx.currentproj.name +'.xpr')
    ictx.vivadoProdPath = join(ictx.currentproj.path, 'products')
    ictx.vivadoProdFileBase = join(ictx.vivadoProdPath, ictx.currentproj.name)

    ictx.vivadoSessions = VivadoSessionManager(keep=lKeep, loglabel=lLogLabel)


# ------------------------------------------------------------------------------
def genproject(ictx, aEnableIPCache, aOptimise, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''

    lSessionId = 'generate-project'

    # Check if vivado is around
    ensureVivado(ictx)

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
            style='red',
        )
        cprint(lExc)
        raise click.Abort()
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def checksyntax(ictx):

    lSessionId = 'chk-syn'

    lStopOn = ['HDL 9-806', 'HDL 9-69']  # Syntax errors  # Type not declared

    # Check that the project exists 
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

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
        "\n{}: Synthax check completed successfully.\n".format(ictx.currentproj.name),
        style='green',
    )

# -------------------------------------
def synth(ictx, aNumJobs, aUpdateInt):
    '''Run synthesis'''

    lSessionId = 'synth'

    # Check that the project exists 
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

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
                lRunProps = { k: v for k, v in readRunInfo(lConsole).items() if lOOCRegex.match(k) }

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
                lConsole('reset_run {}'.format(run))

            # Reset and launch synth_1
            lConsole('reset_run {}'.format(lSynthRun))
            lConsole('launch_runs {} {}'.format(lSynthRun, ' '.join(lArgs)))

            # Monitor OOC and synth run progress
            if not aUpdateInt:
                cprint("Run monitoring disabled", style='cyan')
                lConsole('wait_on_run synth_1')
            else:
                cprint(f"Starting run monitoring loop, update interval: {aUpdateInt} min(s)", style='cyan')
                while True:

                    with VivadoSnoozer(lConsole):
                        lRunProps = readRunInfo(lConsole)

                    lOOCRunProps = { k: v for k, v in lRunProps.items() if lOOCRegex.match(k) }
                    # Reset all OOC synthesis which might are stuck in a running state
                    lPendingOOCRuns = [
                        k for k, v in lOOCRunProps.items()
                        if not v['STATUS'].startswith('synth_design Complete!')
                    ]

                    if lPendingOOCRuns:
                        cprint(makeRunsTable(lOOCRunProps), style='light_sky_blue1')
                    else:
                        cprint(f"OOC runs: {len(lOOCRunProps)} completed.", style='light_sky_blue1')

                    lSynthProps = { k: v for k, v in lRunProps.items() if k == lSynthRun }

                    cprint(makeRunsTable(lSynthProps), style='light_sky_blue1')

                    lRunsInError = [ k for k, v in lRunProps.items() if v['STATUS'] == 'synth_design ERROR']
                    if lRunsInError:
                        raise RuntimeError("Detected runs in ERROR {}. Exiting".format(', '.join(lRunsInError)))

                    # Synthesis finished, get out of there
                    if lRunProps['synth_1']['PROGRESS'] == '100%':
                        break

                    lConsole('wait_on_run synth_1 -timeout {}'.format(aUpdateInt))

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
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

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
                    'reset_run impl_1',
                    'launch_runs impl_1'
                    + (' -jobs {}'.format(aNumJobs) if aNumJobs is not None else ''),
                    'wait_on_run impl_1',
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
def resource_usage(ictx, aCell, aDepth, aFile):

    lSessionId = 'usage'

    # Check that the project exists 
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

    lCmd = 'report_utilization -hierarchical -hierarchical_depth {} -hierarchical_percentages'.format(aDepth)
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

    ensureVivado(ictx)

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
def debugprobes(ictx):
    '''Generate (optional) debug-probes files (used for ILAs and VIO controls).'''

    lSessionId = 'dbg-prb'

    # Check that the project exists.
    ensureVivadoProjPath(ictx.vivadoProjFile)

    lProjName = ictx.currentproj.name
    lDepFileParser = ictx.depParser
    lBaseName = ictx.vivadoProdFileBase

    lBitPath = lBaseName + '.bit'
    if not exists(lBitPath):
        raise click.ClickException("Bitfile does not exist. Can't create debug-probes files.")

    # And that the Vivado ictx is up.
    ensureVivado(ictx)

    lWriteDebugProbesCmd = 'write_debug_probes -force {}'.format(ictx.vivadoProdFileBase+'.ltx')

    try:
        with ictx.vivadoSessions.get(lSessionId) as lConsole:
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
    ensureVivadoProjPath(ictx.vivadoProjFile)



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
    ensureVivado(ictx)
    
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
            f"{ictx.currentproj.name}: {k.capitalize} file successfully written.",
            style='green'
        )

# ------------------------------------------------------------------------------
def readRunInfo(aConsole, aProps=None):
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
def makeRunsTable(aInfos, title=None):
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
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

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
                lInfos = lProject.readRunInfo(lProps)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    lOocTable = makeRunsTable({ k: v for k, v in lInfos.items() if lOOCRegex.match(k)}, title="Out of context runs")
    cprint(lOocTable)
    lDesignRuns = makeRunsTable({ k: v for k, v in lInfos.items() if lRunRegex.match(k)}, title="Design runs")
    cprint(lDesignRuns)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def reset(ictx):
    '''Reset synth and impl runs'''

    lSessionId = 'reset'

    # Check that the project exists 
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

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
    '''Package bitfile with address table and file list

    '''

    ensureVivado(ictx)

    if not exists(ictx.vivadoProjFile):
        cprint('Vivado project does not exist. Creating the project...', style='yellow')
        genproject(ictx, True, True, None, False)

    lProjName = ictx.currentproj.name
    lDepFileParser = ictx.depParser
    lTopEntity = lDepFileParser.settings.get('top_entity', kTopEntity)

    lBaseName = ictx.vivadoProdFileBase
    lBitPath  = lBaseName + '.bit'
    if not exists(lBitPath):
        cprint('Bitfile does not exist. Starting a build ...', style='yellow')
        bitfile(ictx)

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
    console.log("Generating tarball", style='blue')

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
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

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
    ensureVivadoProjPath(ictx.vivadoProjFile)

    # And that the Vivado ictx is up
    ensureVivado(ictx)

    lConsole = ictx.vivadoSessions._getconsole(lSessionId)
    lProject = VivadoProject(lConsole, ictx.vivadoProjFile)
    import IPython

    IPython.embed()

# ------------------------------------------------------------------------------
def validate_settings(ictx):

    v = cerberus.Validator(_schema)
    lSettings = ictx.depParser.settings.dict()
    # Need to convert the settings to a plain dict
    # Need to add a walk-like iterator
    cprint(v.validate(lSettings))
    cprint(v.errors)
