from __future__ import print_function


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Modules
import click
import click_didyoumean

import ipbb
import sys
import traceback

from texttable import Texttable
from click import echo, style, secho

from ..cli import Environment
from .._version import __version__

# ------------------------------------------------------------------------------
# Add -h as default help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
# @shell(
#     prompt=click.style('ipbb', fg='blue') + '> ',
#     intro='Starting IPBus Builder...',
#     context_settings=CONTEXT_SETTINGS
# )
@click.group(
    cls=click_didyoumean.DYMGroup,
    context_settings=CONTEXT_SETTINGS,
)
@click.pass_context
def cli(ctx):
    # Manually add the Environment to the top-level context.
    ctx.obj = Environment()

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@cli.command()
def version():
    echo('ipbb - {}'.format(__version__))
    raise SystemExit(0)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@cli.command()
@click.option('-v', '--verbose', count=True, help="Verbosity")
@click.pass_obj
def info(env, verbose):
    '''Print a brief report about the current working area'''


    if not env.work.path:
        secho  ( 'ERROR: No ipbb work area detected', fg='red' )
        return

    echo  ( )
    secho ( "ipbb environment", fg='blue' )
    # echo  ( "----------------")
    lEnvTable = Texttable(max_width=0)
    lEnvTable.add_row(["Work path", env.work.path])
    if env.currentproj.path:
        lEnvTable.add_row(["Project path", env.currentproj.path])
    echo(lEnvTable.draw())

    if not env.currentproj.path:
        echo  ( )
        secho ( "Firmware packages", fg='blue' )
        lSrcTable = Texttable()
        for lSrc in env.sources:
            lSrcTable.add_row([lSrc])
        echo  ( lSrcTable.draw() )

        echo  ( )
        secho ( "Projects", fg='blue' )
        lProjTable = Texttable()
        for lProj in env.projects:
            lProjTable.add_row([lProj])
        echo  ( lProjTable.draw() )
        return

    echo  ( )

    if env.currentproj.config is None:
        return

    lProjTable = Texttable()
    lProjTable.set_deco(Texttable.VLINES | Texttable.BORDER)

    secho ( "Project '%s'" % env.currentproj.config['name'], fg='blue')
    lProjTable.add_rows([
        # ["name", env.currentproj.config['name']],
        ["toolset", env.currentproj.config['toolset']],
        ["top package", env.currentproj.config['topPkg']],
        ["top component", env.currentproj.config['topCmp']],
        ["top dep file", env.currentproj.config['topDep']],
    ], header=False)
    echo  ( lProjTable.draw() )

    echo  ( )

    secho ( "Dependecy tree elements", fg='blue')
    lCommandKinds = ['setup', 'src', 'addrtab', 'cgpfile']
    lDepTable = Texttable()
    lDepTable.set_cols_align(['c'] * 4)
    lDepTable.add_row(lCommandKinds)
    lDepTable.add_row([len(env.depParser.commands[k]) for k in lCommandKinds])
    echo  ( lDepTable.draw() )

    echo  ( )

    if not env.depParser.missing:
        return
    secho  ( "Unresolved item(s)", fg='red' )

    lUnresolved = Texttable()
    lUnresolved.add_row(["packages", "components", "paths"])
    lUnresolved.add_row([
        len(env.depParser.missingPackages),
        len(env.depParser.missingComponents),
        len(env.depParser.missingPaths )
    ])
    echo ( lUnresolved.draw() )

    echo  ( )

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def main():
    '''Discovers the env at startup'''

    if sys.version_info[0:2] < (2, 6):
        click.secho("Error: I need python 2.6 to run", fg='red')
        raise SystemExit(-1)
    elif sys.version_info[0:2] == (2, 6):
        click.secho("Warning: IPBB prefers python 2.7. python 2.6 will be deprecated soon.", fg='yellow')

    # Add custom cli to shell
    from ..cli import repo
    cli.add_command(repo.init)
    # cli.add_command(repo.cd)
    cli.add_command(repo.add)
    cli.add_command(repo.srcs)

    from ..cli import proj
    cli.add_command(proj.proj)

    from ..cli import dep
    cli.add_command(dep.dep)

    from ..cli import toolbox
    cli.add_command(toolbox.toolbox)

    from ..cli import common

    from ..cli import vivado
    vivado.vivado.add_command(common.cleanup)
    vivado.vivado.add_command(common.addrtab)
    vivado.vivado.add_command(common.gendecoders)
    cli.add_command(vivado.vivado)

    from ..cli import sim
    sim.sim.add_command(common.cleanup)
    sim.sim.add_command(common.addrtab)
    sim.sim.add_command(common.gendecoders)
    cli.add_command(sim.sim)

    from ..cli import debug
    cli.add_command(debug.debug)

    try:
        cli()
    except Exception as e:
        hline = '-'*80
        click.echo()
        click.secho(hline, fg='red')
        click.secho("FATAL ERROR: Caught '"+type(e).__name__+"' exception:", fg='red')
        click.secho(e.message, fg='red')
        click.secho(hline, fg='red')
        import StringIO
        lTrace = StringIO.StringIO()
        traceback.print_exc(file=lTrace)
        print (lTrace.getvalue())
        # Do something with lTrace
        raise SystemExit(-1)
# ------------------------------------------------------------------------------


