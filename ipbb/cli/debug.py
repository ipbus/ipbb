# Modules
import click
import os

# Elements
from click import echo, style, secho

# ------------------------------------------------------------------------------
@click.group()
@click.pass_context
def debug(ctx):
    pass
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command()
@click.pass_context
def dump(ctx):

    if 'IPBB_ROOT' in os.environ:
        echo(os.environ['IPBB_ROOT'])

    env = ctx.obj
    echo('src: '+env.src)
    echo('proj: '+env.proj)
    echo('project: '+env.project)
# ------------------------------------------------------------------------------
