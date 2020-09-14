# Modules
import click
import click_didyoumean
import traceback
import tempfile
import tarfile

from os.path import join, split, exists, basename, abspath, splitext, relpath
from click import echo, secho, style
from ..cmds._utils import echoVivadoConsoleError
from ..tools.common import which
from ..tools.xilinx import VivadoHWServer, VivadoConsoleError
from .._version import __version__


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
@click.pass_context
@click.version_option()
def cli(ctx):
    ctx.obj = ProgEnvironment()


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
    echo('Starting ' + lVivado + '...')
    try:
        v = VivadoHWServer(executable=lVivado, echo=lVerbosity)
        echo('... done')

        echo("Looking for targets")
        v.openHw()
        lConnectedHwServer = v.connect(lHwServerURI)[0]
        lHwTargets = v.getHwTargets()
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
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
        echo("- target " + style(target, fg='blue'))

        try:
            v.openHwTarget(target)
        except VivadoConsoleError as lExc:
            v.closeHwTarget(target)
            continue

        hw_devices = v.getHwDevices()
        for device in hw_devices:
            echo("  + " + style(device, fg='green'))

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
        secho('Extracting {} from {} to {}'.format(lBitFiles[0], bitfile, lTmpDir), fg='green')
        bitfile = join(lTmpDir, lBitFiles[0])

    lHwServerURI = obj.options['vivado.hw_server']

    # Build vivado interface
    lVivado = autodetectVivadoVariant()
    if not lVivado:
        raise click.ClickException(
            "Vivado not found. Please source the Vivado environment before continuing."
        )

    echo('Starting {}...'.format(lVivado))
    try:
        v = VivadoHWServer(executable=lVivado, echo=lVerbosity, stopOnCWarnings=False)
        echo('... done')
        v.openHw()
        v.connect(lHwServerURI)
        hw_targets = v.getHwTargets()

        echo('Found targets: ' + style('{}'.format(', '.join(hw_targets)), fg='blue'))

        lMatchingTargets = [t for t in hw_targets if target in t]
        if len(lMatchingTargets) == 0:
            raise RuntimeError(
                'Target %s not found. Targets available %s: '
                % (target, ', '.join(hw_targets))
            )

        if len(lMatchingTargets) > 1:
            raise RuntimeError(
                'Multiple targets matching %s found. Prease refine your selection. Targets available %s: '
                % (target, ', '.join(hw_targets))
            )

        lTarget = lMatchingTargets[0]

        echo('Selected target: ' + style('{}'.format(lMatchingTargets[0]), fg='blue'))
        v.openHwTarget(lTarget)

        lHWDevices = v.getHwDevices()
        echo('Found devices: ' + style('{}'.format(', '.join(lHWDevices)), fg='blue'))

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
            style(
                "Bitfile {0} will be loaded on {1}.\nDo you want to continue?".format(
                    bitfile, lTarget
                ),
                fg='yellow',
            )
        ):
            echo("Programming {}".format(lTarget))
            v.programDevice(device, bitfile, probe)
            echo("Done.")
            secho(
                "{} successfully programmed on {}".format(bitfile, lTarget), fg='green'
            )
        else:
            secho('Programming aborted.', fg='yellow')
        v.closeHwTarget(lTarget)

    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()


def main():
    '''Discovers the env at startup'''
    try:
        cli()
    except Exception as e:
        hline = '-' * 80
        echo()
        secho(hline, fg='red')
        secho("FATAL ERROR: Caught '" + type(e).__name__ + "' exception:", fg='red')
        secho(e.message, fg='red')
        secho(hline, fg='red')
        import StringIO

        lTrace = StringIO.StringIO()
        traceback.print_exc(file=lTrace)
        print(lTrace.getvalue())
        # Do something with lTrace
        raise SystemExit(-1)
