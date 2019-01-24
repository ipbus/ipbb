# Modules
import click


# ------------------------------------------------------------------------------
@click.group()
@click.pass_context
def debug(ctx):
    from impl.debug import debug
    debug(ctx)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('dump')
@click.pass_context
def dump(ctx):
    from impl.debug import dump
    dump(ctx)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('ipy')
@click.pass_context
def ipy(ctx):
    from impl.debug import ipy
    ipy(ctx)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('test-vivado-formatter')
@click.pass_context
def test_vivado_formatter(ctx):
    from impl.debug import test_vivado_formatter
    test_vivado_formatter(ctx)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command('test-vivado-console')
@click.pass_context
def test_vivado_console(ctx):
    from impl.debug import test_vivado_console
    test_vivado_console(ctx)
