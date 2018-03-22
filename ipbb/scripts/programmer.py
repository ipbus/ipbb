from __future__ import print_function

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Modules
import click
import click_didyoumean
import traceback

from click import echo, secho, style
from ..cli.tools import echoVivadoConsoleError
from ..tools.common import which
from ..tools.xilinx import VivadoConsole, VivadoConsoleError
from .._version import __version__

class ProgEnvironment(object):
    """docstring for ProgEnvironment"""
    def __init__(self):
        super(ProgEnvironment, self).__init__()
        self.arg = arg
        
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
@click.group(
    cls=click_didyoumean.DYMGroup,
    context_settings=CONTEXT_SETTINGS,
)
@click.pass_context
def cli():
    ctx.obj = ProgrammerEnvironment()
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@cli.command()
def version():
    echo('ipb-prog - {}'.format(__version__))
    raise SystemExit(0)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@cli.group()
@click.pass_obj
@click.option('--hwsrv-uri', 'aHwServerURI',default=None, help="Hardware server URI <host>:<port>")
def vivado(obj, aHwServerURI):
    obj.options['vivado.hw_server'] = aHwServerURI
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@vivado.command('list', short_help="Vivado programmer interface.")
@click.pass_obj
@click.option('-v/-q', 'aVerbosity',default=False)
def list(obj, aVerbosity):

    lHwServerURI = obj.options['vivado.hw_server']

    lVivado = autodetectVivadoVariant()
    # Build vivado interface
    echo('Starting '+lVivado+'...')
    try:
        v = VivadoConsole(executable=lVivado, echo=aVerbosity)
        echo('... done')

        echo("Looking for targets")
        v.openHw()
        v.connect(lHwServerURI)
        hw_targets = v.getHwTargets()

        for target in hw_targets:
            echo("- target "+style(target, fg='blue'))

            v.openHwTarget(target)
            hw_devices = v.getHwDevices()
            for device in hw_devices:
                echo("  + "+style(device, fg='green'))
            v.closeHwTarget(target)
    except VivadoConsoleError as lExc:
        echoVivadoConsoleError(lExc)
        raise click.Abort()

# ------------------------------------------------------------------------------   

# ------------------------------------------------------------------------------
def _validateDevice(ctx, param, value):
    lSeparators = value.count(':')
    # Validate the format
    if lSeparators != 1:
        raise click.BadParameter('Malformed device name : %s. Expected <target>:<device>' % value)
    return tuple(value.split(':'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@vivado.command('program')
@click.argument('deviceid', callback=_validateDevice)
@click.argument('bitfile', type=click.Path(exists=True))
@click.option('-v/-q', 'aVerbosity', default=False)
@click.pass_obj
def program(obl, deviceid, bitfile, aVerbosity):

    target, device = deviceid

    lHwServerURI = obj.options['vivado.hw_server']
    
    # Build vivado interface
    lVivado = autodetectVivadoVariant()
    echo('Starting '+lVivado+'...')
    try:
        v = VivadoConsole(executable=lVivado, echo=aVerbosity, stopOnCWarnings=False)
        echo('... done')
        v.openHw()
        v.connect(lHwServerURI)
        hw_targets = v.getHwTargets()

        echo('Found targets: ' + style('{}'.format(', '.join(hw_targets)), fg='blue'))

        lMatchingTargets = [t for t in hw_targets if target in t]
        if len(lMatchingTargets) == 0:
            raise RuntimeError('Target %s not found. Targets available %s: ' % (
                target, ', '.join(hw_targets)))

        if len(lMatchingTargets) > 1:
            raise RuntimeError(
                'Multiple targets matching %s found. Prease refine your selection. Targets available %s: ' % (
                    target, ', '.join(hw_targets)
                )
            )

        lTarget = lMatchingTargets[0]

        echo('Selected target: '+style('{}'.format(lMatchingTargets[0]), fg='blue')) 
        v.openHwTarget(lTarget)

        hw_devs = v.getHwDevices()
        echo('Found devices: '+style('{}'.format(', '.join(hw_devs)), fg='blue'))

        if device not in hw_devs:
            raise RuntimeError('Device %s not found. Devices available %s: ' % (
                device, ', '.join(hw_devs)))

        if click.confirm(style("Bitfile {0} will be loaded on {1}.\nDo you want to continue?".format( bitfile, lTarget), fg='yellow')):
            echo("Programming {}".format(lTarget))
            v.programDevice(device, bitfile)
            echo("Done.")
            secho("{} successfully programmed on {}".format(bitfile, lTarget), fg='green')
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
        hline = '-'*80
        echo()
        secho(hline, fg='red')
        secho("FATAL ERROR: Caught '"+type(e).__name__+"' exception:", fg='red')
        secho(e.message, fg='red')
        secho(hline, fg='red')
        import StringIO
        lTrace = StringIO.StringIO()
        traceback.print_exc(file=lTrace)
        print (lTrace.getvalue())
        # Do something with lTrace
        raise SystemExit(-1)