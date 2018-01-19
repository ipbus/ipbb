from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import sys
import sh

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from click import echo, secho, style, confirm
from texttable import Texttable
from ..tools.common import which, SmartOpen
from .tools import DirSentry, ensureNoMissingFiles


# ------------------------------------------------------------------------------
def ensureVivado(env):
    if env.projectConfig['toolset'] != 'vivado':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivado', found '%s'" % env.projectConfig['toolset'])

    if not which('vivado'):
        # if 'XILINX_VIVADO' not in os.environ:
        raise click.ClickException(
            "Vivado is not available. Have you sourced the environment script?")
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.group(chain=True)
@click.pass_context
@click.option('-p', '--proj', default=None)
def vivado(ctx, proj):
    '''Vivado commands'''

    env = ctx.obj

    lProj = proj if proj is not None else env.project
    if lProj is not None:
        # Change directory before executing subcommand
        from .proj import cd
        ctx.invoke(cd, projname=lProj)
        return
    else:
        if env.project is None:
            raise click.ClickException('Project area not defined. Move into a project area and try again')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def project(env, output):
    '''Assemble the vivado project'''

    lSessionId = 'project'

    # Check if vivado is around
    ensureVivado(env)

    lDepFileParser = env.depParser

    # Ensure thay all dependencies have been resolved
    ensureNoMissingFiles(env.project, lDepFileParser)

    from ..depparser.VivadoProjectMaker import VivadoProjectMaker
    lWriter = VivadoProjectMaker(env.pathMaker)

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with (VivadoOpen(lSessionId) if not output else SmartOpen(output if output != 'stdout' else None)) as lTarget:
            lWriter.write(
                lTarget,
                lDepFileParser.ScriptVariables,
                lDepFileParser.Components,
                lDepFileParser.CommandList,
                lDepFileParser.Libs,
                lDepFileParser.Maps
            )
    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red'
              )
        raise click.Abort()
    except RuntimeError as lExc:
        secho("Error caught while generating Vivado TCL commands:\n" +
              "\n".join(lExc), fg='red'
              )
        raise click.Abort()
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.option('-j', '--jobs', type=int, default=None)
@click.pass_obj
def synth(env, jobs):
    '''Run synthesis'''

    lSessionId = 'synth'

    # Check
    lVivProjPath = join(env.projectPath, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
    ]

    lSynthCmds = [
        'launch_runs synth_1' + (' -jobs {}'.format(jobs) if jobs is not None else ''),
        'wait_on_run synth_1',
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId) as lTarget:
            lTarget(lOpenCmds)
            lTarget(lSynthCmds)
    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red')
        raise click.Abort()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.option('-j', '--jobs', type=int, default=None)
@click.pass_obj
def impl(env, jobs):
    '''Launch implementation run'''

    lSessionId = 'impl'

    # if env.project is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    # Check
    lVivProjPath = join(env.projectPath, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
    ]

    lImplCmds = [
        'launch_runs impl_1' + (' -jobs {}'.format(jobs) if jobs is not None else ''),
        'wait_on_run impl_1',
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId) as lTarget:
            lTarget(lOpenCmds)
            lTarget(lImplCmds)
    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red')
        raise click.Abort()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def bitfile(env):
    '''Create a bitfile'''

    lSessionId = 'bitfile'

    # if env.project is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    # Check
    lVivProjPath = join(env.projectPath, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath)

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
    ]

    lBitFileCmds = [
        'launch_runs impl_1 -to_step write_bitstream',
        'wait_on_run impl_1',
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId) as lTarget:
            lTarget(lOpenCmds)
            lTarget(lBitFileCmds)
    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red')
        raise click.Abort()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def info(env):
    '''Display the current status of project runs'''

    lSessionId = 'info'

    # if env.project is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % join(env.projectPath, 'top', 'top'),
    ]

    lInfos = {}
    lProps = ['status', 'progress']

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId) as lTarget:
            lTarget(lOpenCmds)
            
            lIPs = lTarget('get_ips')[0].split()

            # Gather data about existing runs
            lRuns = lTarget('get_runs')[0].split()
            for lRun in sorted(lRuns):
                secho(lRun, fg='blue')

                lCmds = [ 'get_property {0} [get_runs {1}]'.format(lProp, lRun) for lProp in lProps ]
                lValues = lTarget(lCmds)
                lInfos[lRun] = dict(zip(lProps, lValues))

    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red')
        raise click.Abort()

    echo()
    lSummary = Texttable()
    lSummary.add_row(['']+lProps)
    for lRun in sorted(lInfos):
        lInfo = lInfos[lRun]
        lSummary.add_row([lRun]+[ lInfo[lProp] for lProp in lProps ])
    echo(lSummary.draw())


# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def reset(env):
    '''Reset   runs'''

    lSessionId = 'reset'

    # if env.project is None:
    #     raise click.ClickException(
    #         'Project area not defined. Move into a project area and try again')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % join(env.projectPath, 'top', 'top'),
    ]

    lResetCmds = [
        'reset_run synth_1',
        'reset_run impl_1',
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId) as lTarget:
            lTarget(lOpenCmds)
            lTarget(lResetCmds)
    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red')
        raise click.Abort()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_context
def package(ctx):
    '''Package bitfile with address table and file list'''

    env = ctx.obj

    ensureVivado(env)

    lTopProjPath = 'top'

    if not exists(lTopProjPath):
        secho('Vivado project does not exist. Creating the project...', fg='yellow')
        ctx.invoke(project)


    lBitPath = join(lTopProjPath, 'top.runs', 'impl_1', 'top.bit')
    if not exists(lBitPath):
        secho('Bitfile does not exist. Attempting a build ...', fg='yellow')
        ctx.invoke(bitfile)

    lPkgPath = 'package'
    lSrcPath = join(lPkgPath, 'src')

    # Cleanup first
    sh.rm('-rf', lPkgPath, _out=sys.stdout)

    # Create the folders
    try:
        os.makedirs(join(lSrcPath, 'addrtab'))
    except OSError:
        pass

    # -------------------------------------------------------------------------
    # Generate a json signature file
    import socket
    import time
    secho("Generating summary files", fg='blue')

    # -------------------------------------------------------------------------
    from .dep import hash
    lHash = ctx.invoke(hash, output=join(lSrcPath, 'hashes.txt'), verbose=True)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    lSummary = dict(env.projectConfig)
    lSummary.update({
        'time': socket.gethostname().replace('.', '_'),
        'build host': time.strftime("%a, %d %b %Y %H:%M:%S +0000"),
        'md5': lHash.hexdigest(),
    })

    with SmartOpen(join(lSrcPath, 'summary.txt')) as lSummaryFile:
        import json
        json.dump(lSummary, lSummaryFile.file, indent=2)
    echo()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Copy bitfile and address table into the packaging area
    secho("Collecting bitfile", fg='blue')
    sh.cp('-av', lBitPath, lSrcPath, _out=sys.stdout)
    echo()

    secho("Collecting addresstable", fg='blue')
    # for addrtab in lDepFileParser.CommandList['addrtab']:
    for addrtab in env.depParser.CommandList['addrtab']:
        sh.cp('-av', addrtab.FilePath, join(lSrcPath, 'addrtab'), _out=sys.stdout)
    echo()
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Tar everything up
    secho("Generating tarball", fg='blue')
    lTgzBaseName = '{name}_{host}_{time}'.format(
        name=env.projectConfig['name'],
        host=socket.gethostname().replace('.', '_'),
        time=time.strftime('%y%m%d_%H%M')
    )
    lTgzPath = join(lPkgPath, lTgzBaseName + '.tgz')

    # Zip everything
    sh.tar('cvfz', abspath(lTgzPath), '-C', lPkgPath,
           '--transform', 's/^src/' + lTgzBaseName + '/', 'src', _out=sys.stdout
           )
    echo()

    echo("File " + style('%s' % lTgzPath, fg='green') + " successfully created")
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_context
def archive(ctx):

    lSessionId = 'archive'

    env = ctx.obj

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % join(env.projectPath, 'top', 'top'),
    ]
    lArchiveCmds = [
        'archive_project %s -force' % join(env.projectPath, '{}.xpr.zip'.format(env.projectConfig['name'])),
    ]

    from ..tools.xilinx import VivadoOpen, VivadoConsoleError
    try:
        with VivadoOpen(lSessionId) as lTarget:
            lTarget(lOpenCmds)
            lTarget(lArchiveCmds)
    except VivadoConsoleError as lExc:
        secho("Vivado errors detected\n" +
              "\n".join(lExc.errors), fg='red')
        raise click.Abort()
# ------------------------------------------------------------------------------
