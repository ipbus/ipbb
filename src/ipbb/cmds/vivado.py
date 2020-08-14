from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems
# ------------------------------------------------------------------------------

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
from click import echo, secho, style, confirm
from texttable import Texttable
from collections import OrderedDict

from .dep import hash

from ..tools.common import which, SmartOpen, mkdir
from ._utils import ensureNoParsingErrors, ensureNoMissingFiles, echoVivadoConsoleError

from ..makers.vivadoproject import VivadoProjectMaker
from ..tools.xilinx import VivadoSession, VivadoSessionManager, VivadoConsoleError, VivadoSnoozer, VivadoProject
from ..defaults import kTopEntity

_memCfgKinds = {
    'bin': 'binfile_options',
    'mcs': 'mcsfile_options'
}

# ------------------------------------------------------------------------------
def ensureVivado(env):
    """Utility function guaranteeing the correct Vivado environment.
    
    Args:
        env (ipbb.Environment): Environment object
    
    Raises:
        click.ClickException: Toolset mismatch or Vivado not available
    """
    if env.currentproj.settings['toolset'] != 'vivado':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivado', found '%s'"
            % env.currentproj.settings['toolset']
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
def vivado(env, proj, verbosity, cmdlist):
    '''Vivado command group
    
    Args:
        ctx (click.Context): Command context
        env (ipbb.Environment): Environment object
        proj (str): Project name
        verbosity (str): Verbosity level
    
    Raises:
        click.ClickException: Undefined project area
    '''

    env.vivadoEcho = (verbosity == 'all')

    # lProj = proj if proj is not None else env.currentproj.name
    if proj is not None:
        # Change directory before executing subcommand
        from .proj import cd

        cd(env, projname=proj, aVerbose=False)
        return
    else:
        if env.currentproj.name is None:
            raise click.ClickException(
                'Project area not defined. Move to a project area and try again'
            )

    ensureVivado(env)

    lKeep = True
    lLogLabel = None if not lKeep else '_'.join( cmdlist )

    # Command-specific env variables
    env.vivadoProjPath = join(env.currentproj.path, env.currentproj.name)
    env.vivadoProjFile = join(env.vivadoProjPath, env.currentproj.name +'.xpr')
    env.vivadoProdPath = join(env.currentproj.path, 'products')
    env.vivadoProdFileBase = join(env.vivadoProdPath, env.currentproj.name)

    env.vivadoSessions = VivadoSessionManager(keep=lKeep, loglabel=lLogLabel)


# ------------------------------------------------------------------------------
def makeproject(env, aEnableIPCache, aOptimise, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''

    lSessionId = 'make-project'

    # Check if vivado is around
    ensureVivado(env)

    lDepFileParser = env.depParser

    # Ensure that no parsing errors are present
    ensureNoParsingErrors(env.currentproj.name, lDepFileParser)

    # Ensure that all dependencies are resolved
    ensureNoMissingFiles(env.currentproj.name, lDepFileParser)

    lVivadoIPCache = join(env.work.path, 'var', 'vivado-ip-cache') if aEnableIPCache else None
    lVivadoMaker = VivadoProjectMaker(env.currentproj, lVivadoIPCache, aOptimise)

    if aToScript or aToStdout:
        # Dry run
        lConsoleCtx = SmartOpen(aToScript if not aToStdout else None)
    else:
        lConsoleCtx = env.vivadoSessions.get(lSessionId)

    try:
        with lConsoleCtx as lConsole:
            lVivadoMaker.write(
                lConsole,
                lDepFileParser.config,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        secho(
            "Error caught while generating Vivado TCL commands:\n" + "\n".join(lExc),
            fg='red',
        )
        raise click.Abort()
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def checksyntax(env):

    lSessionId = 'chk-syn'

    lStopOn = ['HDL 9-806', 'HDL 9-69']  # Syntax errors  # Type not declared

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            # Open the project
            lProject = VivadoProject(lConsole, env.vivadoProjFile)

            # Change message severity to ERROR for the isses we're interested in
            lConsole.changeMsgSeverity(lStopOn, 'ERROR')

            # Execute the syntax check
            lConsole('check_syntax')

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho(
        "\n{}: Synthax check completed successfully.\n".format(env.currentproj.name),
        fg='green',
    )

# -------------------------------------
def synth(env, aNumJobs, aUpdateInt):
    '''Run synthesis'''

    lSessionId = 'synth'

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

    lArgs = []

    if aNumJobs is not None:
        lArgs += ['-jobs {}'.format(aNumJobs)]

    lOOCRegex = re.compile(r'.*_synth_\d+')
    lSynthRun = 'synth_1'

    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            # Open the project
            lProject = VivadoProject(lConsole, env.vivadoProjFile)

            with VivadoSnoozer(lConsole):
                lRunProps = { k: v for k, v in iteritems(readRunInfo(lConsole)) if lOOCRegex.match(k) }

            # Reset all OOC synthesis which might are stuck in a running state
            lIPRunsToReset = [
                k for k, v in iteritems(lRunProps)
                if v['STATUS'].startswith('Running')
            ]

            # Reset IP runs, if needed
            for run in lIPRunsToReset:
                secho(
                    'IP run {} found in running state. Resetting.'.format(run),
                    fg='yellow',
                )
                lConsole('reset_run {}'.format(run))

            # Reset and launch synth_1
            lConsole('reset_run {}'.format(lSynthRun))
            lConsole('launch_runs {} {}'.format(lSynthRun, ' '.join(lArgs)))

            # Monitor OOC and synth run progress
            if not aUpdateInt:
                secho("Run monitoring disabled", fg='cyan')
                lConsole('wait_on_run synth_1')
            else:
                secho("Starting run monitoring loop, update interval: {} min(s)".format(aUpdateInt), fg='cyan')
                while True:

                    with VivadoSnoozer(lConsole):
                        lRunProps = readRunInfo(lConsole)

                    lOOCRunProps = { k: v for k, v in iteritems(lRunProps) if lOOCRegex.match(k) }

                    secho('\n' + makeRunsTable(lOOCRunProps).draw(), fg='cyan')

                    lSynthProps = { k: v for k, v in iteritems(lRunProps) if k == lSynthRun }

                    secho('\n' + makeRunsTable(lSynthProps).draw(), fg='cyan')

                    lRunsInError = [ k for k, v in iteritems(lRunProps) if v['STATUS'] == 'synth_design ERROR']
                    if lRunsInError:
                        raise RuntimeError("Detected runs in ERROR {}. Exiting".format(', '.join(lRunsInError)))

                    # Synthesis finished, get out of there
                    if lRunProps['synth_1']['PROGRESS'] == '100%':
                        break

                    lConsole('wait_on_run synth_1 -timeout {}'.format(aUpdateInt))

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        secho(
            "ERROR: \n" + "\n".join(lExc),
            fg='red',
        )
        raise click.Abort()

    secho(
        "\n{}: Synthesis completed successfully.\n".format(env.currentproj.name),
        fg='green',
    )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def impl(env, aNumJobs, aStopOnTimingErr):
    '''
    Launch an implementation run
    '''

 
    lSessionId = 'impl'

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

    lStopOn = []
    if aStopOnTimingErr:
        # List of vivado message that are expected to result into an error.
        lStopOn = ['Timing 38-282']  # Force error when timing is not met

    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:

            # Open the project
            lProject = VivadoProject(lConsole, env.vivadoProjFile)

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
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho(
        "\n{}: Implementation completed successfully.\n".format(env.currentproj.name),
        fg='green',
    )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def resource_usage(env, aCell, aDepth, aFile):

    lSessionId = 'usage'

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

    lCmd = 'report_utilization -hierarchical -hierarchical_depth {} -hierarchical_percentages'.format(aDepth)
    if aCell:
        lCmd += ' -cells ' + aCell

    if aFile:
        lCmd += ' -file ' + aFile
    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, env.vivadoProjFile)
            for c in (
                    'open_run impl_1',
                    lCmd
                ):
                lConsole(c)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()


# ------------------------------------------------------------------------------
def bitfile(env):
    '''Create a bitfile'''

    lSessionId = 'bitfile'

    # Check
    if not exists(env.vivadoProjFile):
        raise click.ClickException("Vivado project %s does not exist" % env.vivadoProjFile)

    ensureVivado(env)

    mkdir(env.vivadoProdPath)
    lWriteBitStreamCmd = 'write_bitstream -force {}'.format(env.vivadoProdFileBase+'.bit')


    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, env.vivadoProjFile)
            lProject.open_run('impl_1')
            lConsole(lWriteBitStreamCmd)

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho(
        "\n{}: Bitfile successfully written.\n".format(env.currentproj.name), fg='green'
    )


# ------------------------------------------------------------------------------
def debugprobes(env):
    '''Generate (optional) debug-probes files (used for ILAs and VIO controls).'''

    lSessionId = 'dbg-prb'

    # Check that the project exists.
    ensureVivadoProjPath(env.vivadoProjFile)

    lProjName = env.currentproj.name
    lDepFileParser = env.depParser
    lBaseName = env.vivadoProdFileBase

    lBitPath = lBaseName + '.bit'
    if not exists(lBitPath):
        raise click.ClickException("Bitfile does not exist. Can't create debug-probes files.")

    # And that the Vivado env is up.
    ensureVivado(env)

    lWriteDebugProbesCmd = 'write_debug_probes -force {}'.format(env.vivadoProdFileBase+'.ltx')

    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, env.vivadoProjFile)
            lProject.open_run('impl_1')
            lConsole(lWriteDebugProbesCmd)

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho(
        "\n{}: Debug probes file successfully written.\n".format(env.currentproj.name), fg='green'
    )


# ------------------------------------------------------------------------------
def memcfg(env):
    '''Create a memcfg file for PROM programming
    
    Supports bin and mcs file types
    Requires the corresponding options to be defined in the dep files:
 
    * bin: 'vivado.binfile_options',
    * mcs: 'vivado.mcsfile_options'
    '''

    lSessionId = 'memcfg'

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)



    lProjName = env.currentproj.name
    lDepFileParser = env.depParser
    # lTopEntity = lDepFileParser.config.get('top_entity', kTopEntity)
    # lBasePath = join(env.vivadoProjPath, lProjName + '.runs', 'impl_1', lTopEntity)
    lBaseName = env.vivadoProdFileBase

    if 'vivado' not in lDepFileParser.config:
        secho('No memcfg settings found in this project. Exiting.', fg='yellow')
        return

    lBitPath = lBaseName + '.bit'
    if not exists(lBitPath):
        raise click.ClickException("Bitfile does not exist. Can't create memcfg files.")

    # And that the Vivado env is up
    ensureVivado(env)
    
    lVivadoCfg = lDepFileParser.config['vivado']
    for k,o in iteritems(_memCfgKinds):

        if o not in lVivadoCfg:
            echo("No configuration found for '{}' files. Skipping.".format(k))
            continue

        lMemCmdOptions = lVivadoCfg[o]
        lMemPath = lBaseName+'.'+k

        try:
            with env.vivadoSessions.get(lSessionId) as lConsole:

                lProject = VivadoProject(lConsole, env.vivadoProjFile)
                lConsole(
                    'write_cfgmem -force -format {} {} -loadbit {{up 0x00000000 "{}" }} -file "{}"'.format(
                        k, lMemCmdOptions, lBitPath, lMemPath
                    )
                )
        except VivadoConsoleError as lExc:
            echoVivadoConsoleError(lExc)
            raise click.Abort()

        secho(
            "\n{}: {}file successfully written.\n".format(k.capitalize(), env.currentproj.name), fg='green'
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
def makeRunsTable(lInfos):
    lSummary = Texttable(max_width=0)
    if not lInfos:
        return lSummary

    # lSummary.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSummary.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSummary.set_chars( ['-', '|', '+', '-'] )
    lSummary.header(['Run'] + list(next(iter(itervalues(lInfos)))))
    for lRun in sorted(lInfos):
        lInfo = lInfos[lRun]
        lSummary.add_row([lRun] + list(itervalues(lInfo)))

    return lSummary


# ------------------------------------------------------------------------------
def status(env):
    '''Show the status of all runs in the current project.'''

    lSessionId = 'status'

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

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
        with env.vivadoSessions.get(lSessionId) as lConsole:
            with VivadoSnoozer(lConsole):
                lProject = VivadoProject(lConsole, env.vivadoProjFile)
                lInfos = lProject.readRunInfo(lProps)

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    echo()

    lOocTable = makeRunsTable({ k: v for k, v in iteritems(lInfos) if lOOCRegex.match(k)})
    secho("Out of context runs", fg='blue')
    echo(lOocTable.draw())
    echo()
    secho("Design runs", fg='blue')
    aaa = makeRunsTable({ k: v for k, v in iteritems(lInfos) if lRunRegex.match(k)})
    echo(aaa.draw())
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def reset(env):
    '''Reset synth and impl runs'''

    lSessionId = 'reset'

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, env.vivadoProjFile)
            for c in (
                    'reset_run synth_1',
                    'reset_run impl_1'
                ):
                lConsole(c)

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

    secho(
        "\n{}: synth_1 and impl_1 successfully reset.\n".format(env.currentproj.name),
        fg='green',
    )
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def package(env, aTag):
    '''Package bitfile with address table and file list

    '''

    ensureVivado(env)

    if not exists(env.vivadoProjFile):
        secho('Vivado project does not exist. Creating the project...', fg='yellow')
        makeproject(env, True, True, None, False)

    lProjName = env.currentproj.name
    lDepFileParser = env.depParser
    lTopEntity = lDepFileParser.config.get('top_entity', kTopEntity)

    lBaseName = env.vivadoProdFileBase
    lBitPath  = lBaseName + '.bit'
    if not exists(lBitPath):
        secho('Bitfile does not exist. Attempting a build ...', fg='yellow')
        bitfile(env)

    try:
        lVivadoCfg = lDepFileParser.config['vivado']
        lActiveMemCfgs = [k for k,o in iteritems(_memCfgKinds) if o in lVivadoCfg]
        lMemCfgFiles = [lBaseName + '.' + k for k in lActiveMemCfgs]

        if any([not exists(f) for f in lMemCfgFiles]):
            memcfg(env)
    except KeyError as e:
        lMemCfgFiles = []

    lDebugProbesPath = lBaseName + '.ltx'
    if not os.path.exists(lDebugProbesPath):
        lDebugProbesPath = None

    # At this point all Vivado manipulations are done. So let's close
    # the Vivado session. Otherwise it will be closed automatically at
    # the end, but in that case it may look confusing because it
    # identifies with the session id from the last Vivado action
    # (which is likely to be 'bitfile' or 'memcfg').
    del env.vivadoSessions

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

    secho("Generating summary files", fg='blue')

    # -------------------------------------------------------------------------

    lHash = hash(env, output=join(lPkgSrcPath, 'hashes.txt'), verbose=True)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    lSummary = dict(env.currentproj.settings)
    lSummary.update(
        {
            'build host': socket.gethostname().replace('.', '_'),
            'time': time.strftime("%a, %d %b %Y %H:%M:%S +0000"),
            'md5': lHash.hexdigest(),
        }
    )

    with open(join(lPkgSrcPath, 'summary.txt'), 'w') as lSummaryFile:
        yaml.safe_dump(lSummary, lSummaryFile, indent=2, default_flow_style=False)
    echo()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Copy bitfile, memcfg, and address table into the packaging area
    secho("Collecting bitfile", fg='blue')
    sh.cp('-av', lBitPath, lPkgSrcPath, _out=sys.stdout)
    echo()

    for f in lMemCfgFiles:
        secho("Collecting memcfg {}".format(f), fg='blue')
        sh.cp('-av', f, lPkgSrcPath, _out=sys.stdout)
        echo()

    if lDebugProbesPath:
        secho("Collecting debug-probes file", fg='blue')
        sh.cp('-av', lDebugProbesPath, lPkgSrcPath, _out=sys.stdout)
        echo()

    secho("Collecting address tables", fg='blue')
    for addrtab in env.depParser.commands['addrtab']:
        sh.cp('-avL', addrtab.filepath, join(lPkgSrcPath, 'addrtab'), _out=sys.stdout)
    echo()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Tar everything up
    secho("Generating tarball", fg='blue')

    lTgzBaseName = '_'.join(
        [env.currentproj.settings['name']]
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
    echo()

    secho(
        "Package " + style('%s' % lTgzPath, fg='green') + " successfully created.",
        fg='green',
    )
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def archive(ctx):

    lSessionId = 'archive'

    env = ctx.obj

    # Check that the project exists 
    ensureVivadoProjPath(env.vivadoProjFile)

    # And that the Vivado env is up
    ensureVivado(env)

    try:
        with env.vivadoSessions.get(lSessionId) as lConsole:
            lProject = VivadoProject(lConsole, env.vivadoProjFile)
            lConsole('archive_project {} -force'.format(
                    join(env.currentproj.path, env.currentproj.settings['name']+'.xpr.zip')
                )
            )
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()


# ------------------------------------------------------------------------------
