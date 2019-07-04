from __future__ import print_function, absolute_import
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Modules
import click
import click_didyoumean

import ipbb
import sys
import traceback
from io import StringIO, BytesIO

from texttable import Texttable
from click import echo, style, secho

from ..cmds import Environment, utils
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
@click.group(cls=click_didyoumean.DYMGroup, context_settings=CONTEXT_SETTINGS)
@click.option('-e', '--exception-stack', 'aExcStack', is_flag=True, help="Display full exception stack")
@click.pass_context
@click.version_option()
def climain(ctx, aExcStack):
    env = ctx.obj

    env.printExceptionStack = aExcStack


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@climain.command()
@click.option('-v', '--verbose', count=True, help="Verbosity")
@click.pass_obj
def info(env, verbose):
    '''Print a brief report about the current working area'''

    if not env.work.path:
        secho('ERROR: No ipbb work area detected', fg='red')
        return

    echo()
    secho("ipbb environment", fg='blue')
    # echo  ( "----------------")
    lEnvTable = Texttable(max_width=0)
    lEnvTable.add_row(["Work path", env.work.path])
    if env.currentproj.path:
        lEnvTable.add_row(["Project path", env.currentproj.path])
    echo(lEnvTable.draw())

    if not env.currentproj.path:
        echo()
        secho("Firmware packages", fg='blue')
        lSrcTable = Texttable()
        lSrcTable.set_deco(Texttable.HEADER | Texttable.BORDER)
        for lSrc in env.sources:
            lSrcTable.add_row([lSrc])
        echo(lSrcTable.draw())

        echo()
        secho("Projects", fg='blue')
        lProjTable = Texttable()
        lProjTable.set_deco(Texttable.HEADER | Texttable.BORDER)
        for lProj in env.projects:
            lProjTable.add_row([lProj])
        echo(lProjTable.draw())
        return

    echo()

    if not env.currentproj.settings:
        return

    # lProjSettingsTable = Texttable()
    # lProjSettingsTable.set_deco(Texttable.VLINES | Texttable.BORDER)

    secho("Project '%s'" % env.currentproj.name, fg='blue')
    # lProjSettingsTable.add_rows([
    #     ["toolset", env.currentproj.settings['toolset']],
    #     ["top package", env.currentproj.settings['topPkg']],
    #     ["top component", env.currentproj.settings['topCmp']],
    #     ["top dep file", env.currentproj.settings['topDep']],
    # ], header=False)
    # echo  ( lProjSettingsTable.draw() )

    echo(utils.formatDictTable(env.currentproj.settings, aHeader=False))

    echo()

    if env.currentproj.usersettings:
        secho("User settings", fg='blue')
        echo(utils.formatDictTable(env.currentproj.usersettings, aHeader=False))

        echo()

    secho("Dependecy tree elements", fg='blue')
    lCommandKinds = ['setup', 'src', 'addrtab', 'iprepo']
    lDepTable = Texttable()
    lDepTable.set_cols_align(['c'] * 4)
    lDepTable.add_row(lCommandKinds)
    lDepTable.add_row([len(env.depParser.commands[k]) for k in lCommandKinds])
    echo(lDepTable.draw())

    echo()

    if not env.depParser.missing:
        return
    secho("Unresolved item(s)", fg='red')

    lUnresolved = Texttable()
    lUnresolved.add_row(["packages", "components", "paths"])
    lUnresolved.add_row(
        [
            len(env.depParser.missingPackages),
            len(env.depParser.missingComponents),
            len(env.depParser.missingPaths),
        ]
    )
    echo(lUnresolved.draw())

    echo()


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def main():
    '''Discovers the env at startup'''

    if sys.version_info[0:2] < (2, 6):
        click.secho("Error: I need python 2.6 to run", fg='red')
        raise SystemExit(-1)
    elif sys.version_info[0:2] == (2, 6):
        click.secho(
            "Warning: IPBB prefers python 2.7. python 2.6 will be deprecated soon.",
            fg='yellow',
        )

    # Add custom cli to shell
    from ..cli import repo

    climain.add_command(repo.init)
    # climain.add_command(repo.cd)
    climain.add_command(repo.add)
    climain.add_command(repo.srcs)

    from ..cli import proj

    climain.add_command(proj.proj)

    from ..cli import dep

    climain.add_command(dep.dep)

    from ..cli import toolbox

    climain.add_command(toolbox.toolbox)

    from ..cli import common

    from ..cli import vivado

    vivado.vivado.add_command(common.cleanup)
    vivado.vivado.add_command(common.addrtab)
    vivado.vivado.add_command(common.gendecoders)
    vivado.vivado.add_command(common.user_config)
    climain.add_command(vivado.vivado)

    from ..cli import sim

    sim.sim.add_command(common.cleanup)
    sim.sim.add_command(common.addrtab)
    sim.sim.add_command(common.gendecoders)
    sim.sim.add_command(common.user_config)
    climain.add_command(sim.sim)

    from ..cli import debug

    climain.add_command(debug.debug)

    obj = Environment()
    try:
        climain(obj=obj)
    except Exception as e:
        from sys import version_info
        exc_type, exc_obj, exc_tb = sys.exc_info()
        lFirstFrame = traceback.extract_tb(exc_tb)[-1]

        secho(
            u"ERROR ('{}' exception caught): '{}'\n\nFile \"{}\", line {}, in {}\n   {}".format(
                exc_type.__name__,
                e,
                lFirstFrame[0],
                lFirstFrame[1],
                lFirstFrame[2],
                lFirstFrame[3],
            ),
            fg='red',
        )

        if obj.printExceptionStack:
            lExc = (BytesIO() if (version_info[0] <= 2) else StringIO())
            traceback.print_exc(file=lExc)
            print("Exception in user code:")
            print('-' * 60)
            secho(lExc.getvalue(), fg='red')
            print('-' * 60)
        raise SystemExit(-1)


# ------------------------------------------------------------------------------
