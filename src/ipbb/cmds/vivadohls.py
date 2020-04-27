from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems
# ------------------------------------------------------------------------------

# Modules
import click

# Elements
from os.path import join, split, exists, splitext, abspath, basename
from click import echo, secho, style, confirm

from ..tools.common import which, SmartOpen
from ._utils import ensureNoParsingErrors, ensureNoMissingFiles, echoVivadoConsoleError

from ..makers.vivadohlsproject import VivadoHlsProjectMaker
from ..tools.xilinx import VivadoHLSOpen, VivadoHLSConsoleError


# ------------------------------------------------------------------------------
def ensureVivadoHLS(env):
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
    ensureVivadoHLS(env)

    lDepFileParser = env.depParser

    # Ensure that no parsing errors are present
    ensureNoParsingErrors(env.currentproj.name, lDepFileParser)

    # Ensure that all dependencies are resolved
    ensureNoMissingFiles(env.currentproj.name, lDepFileParser)

    lVivadoMaker = VivadoHlsProjectMaker(env.currentproj)

    lDryRun = aToScript or aToStdout
    lScriptPath = aToScript if not aToStdout else None

    try:
        with (
            VivadoHLSOpen(lSessionId, echo=env.vivadoHlsEcho) if not lDryRun
            else SmartOpen(lScriptPath)
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


# ------------------------------------------------------------------------------
def synth(env):

    lSessionId = 'synth'

    # Check if vivado is around
    ensureVivadoHLS(env)

    try:
        with VivadoHLSOpen(lSessionId, echo=env.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole('open_project {}'.format(env.currentproj.name))
            lConsole('open_solution sol1')
            lConsole('csynth_design')


    except VivadoHLSConsoleError as lExc:
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
def sim(env):

    lSessionId = 'sim'

    # Check if vivado is around
    ensureVivadoHLS(env)

    try:
        with VivadoHLSOpen(lSessionId, echo=env.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole('open_project {}'.format(env.currentproj.name))
            lConsole('open_solution sol1')
            lConsole('csim_design')


    except VivadoHLSConsoleError as lExc:
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
def cosim(env):
    lSessionId = 'cosim'

    # Check if vivado is around
    ensureVivadoHLS(env)

    try:
        with VivadoHLSOpen(lSessionId, echo=env.vivadoHlsEcho) as lConsole:

            # Open the project
            lConsole('open_project {}'.format(env.currentproj.name))
            lConsole('open_solution sol1')
            lConsole('cosim_design')


    except VivadoHLSConsoleError as lExc:
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
    