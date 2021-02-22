
# Modules
import click


# ------------------------------------------------------------------------------
@click.group('debug', help='Collection of debug/utility commands')
@click.pass_obj
def debug(ictx):
    """Collection of debug/utility commands
    
    Args:
        ictx (`obj`): Context object.
    """
    from ..cmds.debug import debug
    debug(ictx)


# ------------------------------------------------------------------------------
@debug.command('dump')
@click.pass_obj
def dump(ictx):
    from ..cmds.debug import dump
    dump(ictx)


# ------------------------------------------------------------------------------
@debug.command('ipy', help='Loads the ipbb environment and opens a python shell')
@click.pass_obj
@click.pass_context
def ipy(ctx, ictx):
    """Loads the ipbb environment and opens a python shell
    
    Args:
        ictx (`obj:Context`): Context object.
    """
    from ..cmds.debug import ipy
    ipy(ctx, ictx)


# ------------------------------------------------------------------------------
@debug.command('test-vivado-formatter', help='Test Vivado formatter')
@click.pass_obj
def test_vivado_formatter(ictx):
    """Test vivado formatter
    
    Args:
        ictx (`obj:Context`): Context object.
    """
    from ..cmds.debug import test_vivado_formatter
    test_vivado_formatter(ictx)


# ------------------------------------------------------------------------------
@debug.command('test-vivado-console', help='Test Vivado console')
@click.pass_obj
def test_vivado_console(ictx):
    """Test Vivado console
    
    Args:
        ictx (`obj:Context`): Context object.
    """
    from ..cmds.debug import test_vivado_console
    test_vivado_console(ictx)
