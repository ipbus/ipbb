
import click

# ------------------------------------------------------------------------------
@click.group('ipbus', help='Collection of IPbus-specific commands')
@click.pass_obj
def ipbus(env):
    """Collection of ipbus specific commands
    
    Args:
        env (`obj`): Context object.
    """
    from ..cmds.ipbus import ipbus
    ipbus(env)


# ------------------------------------------------------------------------------
@ipbus.command(
    'gendecoders',
    help='Generate or update the ipbus address decoders references by dep files.',
)
@click.option('-c', '--check-up-to-date', 'aCheckUpToDate', is_flag=True, help='Checks for out-of-date or missing decoders. Returns error if any of the two are found.')
@click.option('-f', '--force', 'aForce', is_flag=True, help='Force an update of the address decodes without asking for confirmation.')
@click.option('-t', '--template', 'aTemplate', type=click.Path(), help='Path to IPbus address decoder VHDL template.')
@click.pass_obj
def gendecoders(env, aCheckUpToDate, aForce, aTemplate):
    """Generates the ipbus address decoder modules
    
    Args:
        env (`obj`): Click context
    """
    from ..cmds.ipbus import gendecoders
    gendecoders(env, aCheckUpToDate, aForce, aTemplate)
