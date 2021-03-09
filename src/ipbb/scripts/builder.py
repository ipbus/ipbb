# Modules
import click
import click_didyoumean

import ipbb
import sys
import traceback
from io import StringIO, BytesIO

from texttable import Texttable
from click import echo, style, secho

from ..context import Context

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
def _compose_cli():
    # Add custom cli to shell
    from ..cli import repo

    climain.add_command(repo.init)
    climain.add_command(repo.info)
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
    vivado.vivado.add_command(common.user_config)
    climain.add_command(vivado.vivado)

    from ..cli import sim

    sim.sim.add_command(common.cleanup)
    sim.sim.add_command(common.addrtab)
    sim.sim.add_command(common.user_config)
    climain.add_command(sim.sim)

    from ..cli import vivadohls

    vivadohls.vivadohls.add_command(common.cleanup)
    climain.add_command(vivadohls.vivadohls)

    from ..cli import ipbus
    climain.add_command(ipbus.ipbus)

    from ..cli import debug

    climain.add_command(debug.debug)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def main():
    '''Discovers the env at startup'''

    if sys.version_info[0:2] < (2, 7):
        click.secho("Error: Python 2.7 is required to run IPBB", fg='red')
        raise SystemExit(-1)

    _compose_cli()

    obj = Context()
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
