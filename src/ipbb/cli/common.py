from __future__ import print_function, absolute_import


import click


# ------------------------------------------------------------------------------
@click.command(
    'cleanup',
    short_help="Clean up the project directory. Delete all files and folders.",
)
@click.pass_obj
@click.pass_context
def cleanup(ctx, *args, **kwargs):
    """Clean the current project area.

    Removes all files except for .ipbbproj
    
    Args:
        env (`obj`): ipbb environment object
    """
    from ..cmds.common import cleanup
    return (ctx.command.name, cleanup, args, kwargs)

# ------------------------------------------------------------------------------
@click.command('user-config', short_help="Manage project-wise user settings.")
@click.option('-l', '--list', 'aList', is_flag=True)
@click.option('-a', '--add', 'aAdd', nargs=2, help='Add a new variable: name value')
@click.option('-u', '--unset', 'aUnset', nargs=1, help='Remove a variable: name')
@click.pass_obj
@click.pass_context
def user_config(ctx, *args, **kwargs):
    """Displays, sets and manage user settings of the current project
    
    Args:
        env (`obj`): ipbb environment object
        aList (bool): 'list' flag
        aAdd (bool): 'add' flag
        aUnset (bool): 'unset' flag
    """
    from ..cmds.common import user_config
    return (ctx.command.name, user_config, args, kwargs)


# ------------------------------------------------------------------------------
@click.command('addrtab', short_help="Gather address table files.")
@click.pass_obj
@click.option('-d', '--dest', 'aDest', default='addrtab')
@click.pass_context
def addrtab(ctx, *args, **kwargs):
    '''Copy address table files into addrtab subfolder
    
    Args:
        env (`obj`): ipbb environment object
        aDest (string): Target address table folder
    '''
    from ..cmds.common import addrtab
    return (ctx.command.name, addrtab, args, kwargs)
