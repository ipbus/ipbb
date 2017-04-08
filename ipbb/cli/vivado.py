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
from click import echo, secho, style
from ..tools.common import which, SmartOpen
from .common import DirSentry


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
    '''Vivado command group'''
    if proj is None:
        return

    # Change directory before executing subcommand
    from .proj import cd
    ctx.invoke(cd, projname=proj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def project(env, output):
    '''Assemble current vivado project'''

    lSessionId = 'project'

    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

    ensureVivado(env)

    # lDepFileParser, lPathmaker, lCommandLineArgs = makeParser( env, 3 )
    lDepFileParser = env.depParser

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
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# @vivado.command()
# @click.pass_obj
# def inspect(env):
#     lSessionId = 'inspect'

#     if env.project is None:
#         raise click.ClickException(
#             'Project area not defined. Move into a project area and try again')

#     lVivProjPath = join(env.projectPath, 'top', 'top.xpr')

#     if not exists(lVivProjPath):
#         raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

#     lOpenCmds = [
#         'open_project %s' % lVivProjPath,
#     ]

#     lInspectCmds = [
#         'get_property PROGRESS [get_runs synth_1]',
#         'get_property PROGRESS [get_runs impl_1]'
#     ]

#     from ..tools.xilinx import VivadoOpen, VivadoConsoleError
#     try:
#         with VivadoOpen(lSessionId) as lTarget:
#             lTarget(lOpenCmds)
#             lTarget(lInspectCmds)
#     except VivadoConsoleError as lExc:
#         secho("Vivado errors detected\n" +
#               "\n".join(lExc.errors), fg='red'
#               )
#         raise click.Abort()


# ------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def synth(env):
    '''Syntesize and implement current vivado project'''

    lSessionId = 'synth'

    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

    # Check
    lVivProjPath = join(env.projectPath, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
    ]

    lSynthCmds = [
        'launch_runs synth_1',
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
@click.pass_obj
def impl(env):
    '''Syntesize and implement current vivado project'''

    lSessionId = 'impl'

    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

    # Check
    lVivProjPath = join(env.projectPath, 'top', 'top.xpr')
    if not exists(lVivProjPath):
        raise click.ClickException("Vivado project %s does not exist" % lVivProjPath, fg='red')

    ensureVivado(env)

    lOpenCmds = [
        'open_project %s' % lVivProjPath,
    ]

    lImplCmds = [
        'launch_runs impl_1',
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
    lSessionId = 'bitfile'

    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

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
def reset(env):
    lSessionId = 'reset'

    if env.project is None:
        raise click.ClickException(
            'Project area not defined. Move into a project area and try again')

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
    '''List address table files'''

    env = ctx.obj

    ensureVivado(env)

    lBitPath = join('top', 'top.runs', 'impl_1', 'top.bit')
    if not exists(lBitPath):
        # raise click.ClickException(
            # "Bitfile {0} not found. Please run 'bitfile' command first.".format(lBitPath))
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
