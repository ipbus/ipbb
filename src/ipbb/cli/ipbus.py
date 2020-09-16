
import click

# ------------------------------------------------------------------------------
@click.group()
@click.pass_obj
def ipbus(env):
    """Collection of ipbus specific commands
    
    Args:
        env (`obj`): Environment object.
    """
    from ..cmds.ipbus import ipbus
    ipbus(env)


# ------------------------------------------------------------------------------
@ipbus.command(
    'gendecoders',
    short_help='Generate or update the ipbus address decoders references by dep files.',
)
@click.option('-c', '--check-up-to-date', 'aCheckUpToDate', is_flag=True, help='Checks for out-of-date or missing decoders. Returns error if any of the two are found.')
@click.option('-f', '--force', 'aForce', is_flag=True, help='Force an update of the address decodes without asking for confirmation.')
@click.pass_obj
def gendecoders(env, aCheckUpToDate, aForce):
    """Generates the ipbus address decoder modules
    
    Args:
        env (`obj`): Click context
    """
    from ..cmds.ipbus import gendecoders
    gendecoders(env, aCheckUpToDate, aForce)
