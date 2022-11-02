# Modules
import click
import click_didyoumean
import traceback
import tempfile
import tarfile

from os.path import join, split, exists, basename, abspath, splitext, relpath
# from click import echo, secho, style
from rich.text import Text
from ..console import cprint, console
from ..utils import logVivadoConsoleError
from ..utils import which
from ..tools.xilinx import VivadoHWServer, VivadoConsoleError
from .. import __version__


class ProgEnvironment(object):
    """docstring for ProgEnvironment"""

    def __init__(self):
        super().__init__()
        self.options = {}


# ------------------------------------------------------------------------------
# Add -h as default help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
# ------------------------------------------------------------------------------


def autodetectVivadoVariant():

    lCandidates = ['vivado_lab', 'vivado']

    for lCandidate in lCandidates:
        if which(lCandidate) is None:
            continue
        return lCandidate


# ------------------------------------------------------------------------------
# @shell(
#     prompt=style('ipbb', fg='blue') + '> ',
#     intro='Starting IPBus Builder...',
#     context_settings=CONTEXT_SETTINGS
# )
@click.group(cls=click_didyoumean.DYMGroup, context_settings=CONTEXT_SETTINGS)
@click.option('-e', '--exception-stack', 'aExcStack', is_flag=True, help="Display full exception stack")
@click.pass_context
@click.version_option()
def cli(ctx, aExcStack):
    ictx = ctx.obj

    ictx.printExceptionStack = aExcStack



# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@cli.group()
@click.pass_obj
@click.option('-v/-q', 'aVerbosity', default=False, help="Verbose output.")
@click.option(
    '--hwsrv-uri',
    'aHwServerURI',
    default=None,
    help="Hardware server URI <host>:<port>",
)
@click.option(
    '--add-xvc',
    'aVirtualCables',
    default=[],
    help="Add virtual cable <host>:<port>",
    multiple=True,
)
def vivado(obj, aVerbosity, aHwServerURI, aVirtualCables):
    obj.options['vivado.verbosity'] = aVerbosity
    obj.options['vivado.hw_server'] = aHwServerURI
    obj.options['vivado.virtualcables'] = aVirtualCables
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@vivado.command('list', short_help="Vivado programmer interface.")
@click.pass_obj
def list(obj):

    lVerbosity = obj.options['vivado.verbosity']
    lHwServerURI = obj.options['vivado.hw_server']
    lVirtualCables = obj.options['vivado.virtualcables']

    lVivado = autodetectVivadoVariant()
    if not lVivado:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing."
        )

    # Build vivado interface
    cprint(f"Starting {lVivado}...")
    try:
        v = VivadoHWServer(executable=lVivado, echo=lVerbosity)
        cprint("... done")

        cprint("Looking for targets")
        v.openHw()
        lConnectedHwServer = v.connect(lHwServerURI)[0]
        lHwTargets = v.getHwTargets()
    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()

    if lVirtualCables:
        for vc in lVirtualCables:
            lVCTarget = lConnectedHwServer + '/xilinx_tcf/Xilix/' + vc
            if lVCTarget in lHwTargets:
                continue

            # for lRetries in range(5):
            try:
                v.openHwTarget(vc, is_xvc=True)
                v.closeHwTarget()
            except VivadoConsoleError as lExc:
                continue
            break
            # Update the list
            # lHwTargets = v.getHwTargets()
            lHwTargets += [lVCTarget]

    for target in lHwTargets:
        cprint(f"- target [blue]{traget}[/blue]")

        try:
            v.openHwTarget(target)
        except VivadoConsoleError as lExc:
            v.closeHwTarget(target)
            continue

        hw_devices = v.getHwDevices()
        for device in hw_devices:
            cprint(f"  + [green]{device}[/green]")

        v.closeHwTarget(target)


# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def _validateDevice(ctx, param, value):
    lSeparators = value.count(':')
    # Validate the format
    if lSeparators == 0:
        return (value, None)
    elif lSeparators == 1:
        return tuple(value.split(':'))
    else:
        raise click.BadParameter(
            'Malformed device name : %s. Expected <target>:<device>' % value
        )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command('program')
@click.argument('deviceid', callback=_validateDevice)
@click.argument('bitfile', type=click.Path(exists=True))
@click.option('-p', '--probe', type=click.Path(), default=None, help="Probe file")
@click.option('-y', 'yes', is_flag=True, default=False, help="Proceed with asking for confirmation.")
@click.pass_obj
def program(obj, deviceid, bitfile, probe, yes):

    lVerbosity = obj.options['vivado.verbosity']

    target, device = deviceid

    bitbase, bitext = splitext(bitfile)
    if bitext == '.tgz':
        # Memento: delete tempdir
        lTmpDir = tempfile.mkdtemp()
        with tarfile.open(bitfile) as lTF:
            lBitFiles = [m.name for m in lTF.getmembers() if m.name.endswith('.bit')]
            if len(lBitFiles) < 0:
                raise RuntimeError('No .bit images found in {}'.format(bitfile))
            elif len(lBitFiles) > 1:
                raise RuntimeError(
                    'Multiple .bit images found in {}: {}'.format(bitfile, ' '.join(lBitFiles))
                )

            lTF.extract(lBitFiles[0], lTmpDir)
        cprint(f"Extracting {lBitFiles[0]} from {bitfile} to {lTmpDir}", style='green')
        bitfile = join(lTmpDir, lBitFiles[0])

    lHwServerURI = obj.options['vivado.hw_server']

    # Build vivado interface
    lVivado = autodetectVivadoVariant()
    if not lVivado:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing."
        )

    cprint(f"Starting {lVivado}...")
    try:
        v = VivadoHWServer(executable=lVivado, echo=lVerbosity, stopOnCWarnings=False)
        cprint("... done")
        v.openHw()
        v.connect(lHwServerURI)
        hw_targets = v.getHwTargets()

        cprint(f"Found targets: [blue]{', '.join(hw_targets)}[/blue]")

        lMatchingTargets = [t for t in hw_targets if target in t]
        if len(lMatchingTargets) == 0:
            raise RuntimeError(
                f"Target {target} not found. Targets available: {', '.join(hw_targets)}"
            )

        if len(lMatchingTargets) > 1:
            raise RuntimeError(
                f"Multiple targets matching {target} found. Prease refine your selection. Targets available: {', '.join(hw_targets)}"
            )

        lTarget = lMatchingTargets[0]

        cprint(f"Selected target: [blue]{lMatchingTargets[0]}[/blue]")
        v.openHwTarget(lTarget)

        lHWDevices = v.getHwDevices()
        cprint(f"Found devices: [blue]{', '.join(lHWDevices)}[/blue]")
        # echo('Found devices: ' + style('{}'.format(', '.join(lHWDevices)), fg='blue'))

        if device is None:
            if len(lHWDevices) == 1:
                device = lHWDevices[0]
            else:
                raise RuntimeError(
                    'Device not specified while multiple devices are available at the current target {}: {} '.format(
                        lTarget, ', '.join(lHWDevices)
                    )
                )
        elif device not in lHWDevices:
            raise RuntimeError(
                'Device %s not found. Devices available %s: '
                % (device, ', '.join(lHWDevices))
            )

        if yes or click.confirm(
            Text(f"Bitfile {bitfile} will be loaded on {lTarget}.\nDo you want to continue?", style='yellow')
        ):
            cprint(f"Programming {lTarget}")
            v.programDevice(device, bitfile, probe)
            cprint("Done.")
            cprint(f"{bitfile} successfully programmed on {lTarget}", style='green')
        else:
            cprint(f"Programming aborted.", style='yellow')
        v.closeHwTarget(lTarget)

    except VivadoConsoleError as lExc:
        logVivadoConsoleError(lExc)
        raise click.Abort()


def main():
    '''Discovers the env at startup'''
    obj = ProgEnvironment()

    try:
        cli(obj=obj, show_default=True)
    except Exception as e:
        cprint("ERROR: exception caught!", style='red')
        cprint(e, style='red')

        if obj.printExceptionStack:
            console.print_exception()

        raise SystemExit(-1)
