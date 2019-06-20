from __future__ import print_function, absolute_import


# Modules
import click


# ------------------------------------------------------------------------------
@click.group()
@click.pass_env
def debug(env):
    """Collection of debug/utility commands
    
    Args:
        env (`obj`): Environment object.
    """
    from ..cmds.debug import debug
    debug(env)


# ------------------------------------------------------------------------------
@debug.command('dump')
@click.pass_env
def dump(env):
    from ..cmds.debug import dump
    dump(env)


# ------------------------------------------------------------------------------
@debug.command('ipy')
@click.pass_env
def ipy(env):
    """Loads the ipbb environment and opens a python shell
    
    Args:
        env (`obj:Context`): Environment object.
    """
    from ..cmds.debug import ipy
    ipy(env)


# ------------------------------------------------------------------------------
@debug.command('test-vivado-formatter')
@click.pass_env
def test_vivado_formatter(env):
    """Test vivado formatter
    
    Args:
        env (`obj:Context`): Environment object.
    """
    from ..cmds.debug import test_vivado_formatter
    test_vivado_formatter(env)


# ------------------------------------------------------------------------------
@debug.command('test-vivado-console')
@click.pass_env
def test_vivado_console(env):
    """Test Vivado console
    
    Args:
        env (`obj:Context`): Environment object.
    """
    from ..cmds.debug import test_vivado_console
    test_vivado_console(env)
