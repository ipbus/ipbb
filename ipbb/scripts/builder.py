from __future__ import print_function


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Modules
import click
import click_didyoumean

import ipbb
import sys

from texttable import Texttable

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

    from ..cli import Environment
    # Manually add the Environment to the top-level context.
    ctx.obj = Environment()

    # Print warning message if in command-line mode (no arguments) and we are not in an ipbb area.
    # if not ctx.protected_args and not ctx.invoked_subcommand:
        # print (ctx.obj)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@cli.command()
@click.option('-v', '--verbose', count=True, help='arse')
@click.pass_obj
def info(env, verbose):
    '''Print a brief report about the current working area'''

    from click import echo, style, secho

    if not env.workPath:
        secho  ( 'ERROR: No ipbb work area detected', fg='red' )
        return

    echo  ( )
    secho ( "ipbb environment", fg='blue' )
    # echo  ( "----------------")
    lEnvTable = Texttable(max_width=0)
    lEnvTable.add_row(["Work path", env.workPath])
    if env.projectPath:
        lEnvTable.add_row(["Project path", env.projectPath])
    echo(lEnvTable.draw())

    if not env.projectPath:
        echo  ( )
        secho ( "Firmware packages", fg='blue' )
        # echo  ( "---------------")
        # for s in env.getSources():
        #     echo ( "  - " + s )
        lSrcTable = Texttable()
        for lSrc in env.getSources():
            lSrcTable.add_row([lSrc])
        echo  ( lSrcTable.draw() )

        echo  ( )
        secho ( "Projects", fg='blue' )
        # echo  ( "--------")
        # for p in env.getProjects():
        #     echo ( "  - " + p )
        # echo  ( )
        lProjTable = Texttable()
        for lProj in env.getProjects():
            lProjTable.add_row([lProj])
        echo  ( lProjTable.draw() )
        return

    echo  ( )

    if env.projectConfig is None:
        return

    lProjTable = Texttable()
    lProjTable.set_deco(Texttable.VLINES | Texttable.BORDER)

    secho ( "Project '%s'" % env.projectConfig['name'], fg='blue')
    lProjTable.add_rows([
        # ["name", env.projectConfig['name']],
        ["toolset", env.projectConfig['toolset']],
        ["top package", env.projectConfig['topPkg']],
        ["top component", env.projectConfig['topCmp']],
        ["top dep file", env.projectConfig['topDep']],
    ], header=False)
    echo  ( lProjTable.draw() )

    echo  ( )

    secho ( "Dependecy tree elements", fg='blue')
    lCommandKinds = ['setup', 'src', 'addrtab', 'cgpfile']
    lDepTable = Texttable()
    lDepTable.set_cols_align(['c'] * 4)
    lDepTable.add_row(lCommandKinds)
    lDepTable.add_row([len(env.depParser.CommandList[k]) for k in lCommandKinds])
    echo  ( lDepTable.draw() )

    echo  ( )

    if not env.depParser.NotFound:
        return
    secho  ( "Unresolved item(s)", fg='red' )

    lUnresolved = Texttable()
    lUnresolved.add_row(["packages", "components", "paths"])
    lUnresolved.add_row([
        len(env.depParser.PackagesNotFound),
        len(env.depParser.ComponentsNotFound),
        len(env.depParser.PathsNotFound )
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

    from ..cli import proj
    cli.add_command(proj.proj)

    from ..cli import dep
    cli.add_command(dep.dep)

    from ..cli import vivado
    cli.add_command(vivado.vivado)

    from ..cli import sim
    cli.add_command(sim.sim)

    from ..cli import debug
    cli.add_command(debug.debug)
    
    try:
        cli()
    except Exception as e:
        click.secho(str(e), fg='red')
# ------------------------------------------------------------------------------


