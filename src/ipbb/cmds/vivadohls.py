from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems
# ------------------------------------------------------------------------------

# Modules
import click

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from click import echo, secho, style, confirm

from ..tools.common import which, SmartOpen

from ..makers.vivadohlsproject import VivadoHlsProjectMaker
from ..tools.xilinx import VivadoHLSOpen, VivadoHLSConsoleError


# ------------------------------------------------------------------------------
def ensureVivado(env):
    if env.currentproj.settings['toolset'] != 'vivadohls':
        raise click.ClickException(
            "Work area toolset mismatch. Expected 'vivadohls', found '%s'"
            % env.currentproj.settings['toolset']
        )

    if not which('vivado_hls'):
        # if 'XILINX_VIVADO' not in os.environ:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing."
        )


# ------------------------------------------------------------------------------
def vivadohls(env, proj, verbosity):
    '''Vivado command group'''

    env.vivadoHlsEcho = (verbosity == 'all')

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

    env.vivadoHlsProjPath = join(env.currentproj.path, env.currentproj.name)
    # env.vivadoHlsProjFile = join(env.vivadoProjPath, env.currentproj.name +'.xpr')


# ------------------------------------------------------------------------------
def makeproject(env, aToScript, aToStdout):
    '''Make the Vivado project from sources described by dependency files.'''

    lSessionId = 'make-project'

    # Check if vivado is around
    ensureVivado(env)

    lDepFileParser = env.depParser

    lVivadoMaker = VivadoHlsProjectMaker(env.currentproj)

    lDryRun = aToScript or aToStdout

    try:
        with (
            VivadoHLSOpen(lSessionId, echo=env.vivadoHlsEcho)
            if not lDryRun
            else SmartOpen(
                # Dump to script
                aToScript
                if not aToStdout
                # Dump to terminal
                else None
            )
        ) as lConsole:

            lVivadoMaker.write(
                lConsole,
                lDepFileParser.config,
                lDepFileParser.packages,
                lDepFileParser.commands,
                lDepFileParser.libs,
            )

    except VivadoHLSConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()
    except RuntimeError as lExc:
        secho(
            "Error caught while generating Vivado TCL commands:\n" + "\n".join(lExc),
            fg='red',
        )
        raise click.Abort()
    # -------------------------------------------------------------------------

