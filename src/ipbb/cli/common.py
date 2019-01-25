from __future__ import print_function


import click


# ------------------------------------------------------------------------------
@click.command(
    'cleanup',
    short_help="Clean up the project directory. Delete all files and folders.",
)
@click.pass_obj
def cleanup(env):
    """Clean the current project area.

    Removes all files except for .ipbbproj
    
    Args:
        env (`obj`): ipbb environment object
    """
    from impl.common import cleanup
    cleanup(env)

# ------------------------------------------------------------------------------
@click.command('user-config', short_help="Manage project-wise user settings.")
@click.option('-l', '--list', 'aList', is_flag=True)
@click.option('-a', '--add', 'aAdd', nargs=2, help='Add a new variable: name value')
@click.option('-u', '--unset', 'aUnset', nargs=1, help='Remove a variable: name')
@click.pass_obj
def user_config(env, aList, aAdd, aUnset):
    """Displays, sets and manage user settings of the current project
    
    Args:
        env (`obj`): ipbb environment object
        aList (bool): 'list' flag
        aAdd (bool): 'add' flag
        aUnset (bool): 'unset' flag
    """
    from impl.common import user_config
    user_config(env, aList, aAdd, aUnset)


# ------------------------------------------------------------------------------
@click.command('addrtab', short_help="Gather address table files.")
@click.pass_obj
@click.option('-d', '--dest', 'aDest', default='addrtab')
def addrtab(env, aDest):
    '''Copy address table files into addrtab subfolder
    
    Args:
        env (`obj`): ipbb environment object
        aDest (string): Target address table folder
    '''
    from impl.common import addrtab
    addrtab(env, aDest)

# ------------------------------------------------------------------------------
@click.command(
    'gendecoders',
    short_help='Generate or update the ipbus address decoders references by dep files.',
)
@click.pass_context
def gendecoders(ctx):
    """Generates the ipbus address decoder modules
    
    Args:
        ctx (`obj`): Click context
    """
    from impl.common import gendecoders
    gendecoders(ctx)