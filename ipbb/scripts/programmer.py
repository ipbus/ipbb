from __future__ import print_function

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Modules
import click
import click_didyoumean

from ..tools.common import which

# ------------------------------------------------------------------------------
# Add -h as default help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
# ------------------------------------------------------------------------------

def detectVivadoVariant():

    lCandidates = ['vivado_lab', 'vivado']

    for lCandidate in lCandidates:
        if which(lCandidate) is None:
            continue
        return lCandidate

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
def cli():
    pass
# ------------------------------------------------------------------------------

@cli.group()
@click.pass_context
def vivado(ctx):
    pass

# ------------------------------------------------------------------------------
@vivado.command()
@click.option('-v/-q', default=False)
def list(v):
    lVivado = detectVivadoVariant()
    # Build vivado interface
    click.echo('Starting '+lVivado+'...')
    from ..tools import xilinx
    v = xilinx.VivadoConsole(executable=lVivado, echo=v)
    click.echo('... done')

    click.echo("Looking for targets")
    v.openHw()
    v.connect()
    hw_targets = v.getHwTargets()

    for target in hw_targets:
        click.echo("- target "+click.style(target, fg='blue'))

        v.openHwTarget(target)
        hw_devices = v.getHwDevices()
        for device in hw_devices:
            click.echo("  + "+click.style(device, fg='green'))
        v.closeHwTarget(target)

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
@vivado.command()
@click.argument('deviceid', callback=_validateDevice)
@click.argument('bitfile', type=click.Path(exists=True))
@click.option('-v/-q', default=False)
def program(deviceid, bitfile, v):

    target, device = deviceid
    # Build vivado interface
    
    lVivado = detectVivadoVariant()
    click.echo('Starting '+lVivado+'...')
    from ..tools import xilinx
    v = xilinx.VivadoConsole(executable=lVivado, echo=v)
    click.echo('... done')
    v.openHw()
    v.connect()
    hw_targets = v.getHwTargets()

    click.echo('Found targets: ' + click.style('{}'.format(', '.join(hw_targets)), fg='blue'))

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

    click.echo('Selected target: '+click.style('{}'.format(lMatchingTargets[0]), fg='blue')) 
    v.openHwTarget(lTarget)

    hw_devs = v.getHwDevices()
    click.echo('Found devices: '+click.style('{}'.format(', '.join(hw_devs)), fg='blue'))

    if device not in hw_devs:
        raise RuntimeError('Device %s not found. Devices available %s: ' % (
            device, ', '.join(hw_devs)))

    if click.confirm("Bitfile {0} will be loaded on {1}. Do you want to continue?".format( bitfile, lTarget)):
        v.programDevice(device, bitfile)
        click.echo("{} successfully programmed on {}".format(bitfile, lTarget))
    else:
        click.secho('Skipping programming stage', fg='yellow')
    v.closeHwTarget(lTarget)


def main():
    '''Discovers the env at startup'''
    try:
        cli()
    except Exception as e:
        click.secho(str(e), fg='red')