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
        echo(style('IPBB_ROOT', fg='blue')+': '+os.environ['IPBB_ROOT'])

    env = ctx.obj
    echo(style('src dir', fg='blue')+': '+env.srcdir)
    echo(style('proj dir', fg='blue')+': '+env.projdir)
    echo(style('project name', fg='blue')+': '+env.currentproj.name)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@debug.command()
@click.pass_context
def ipy(ctx):
    '''Opens IPython to inspect the parser'''
    # env = ctx.obj

    import IPython
    IPython.embed()
# ------------------------------------------------------------------------------
