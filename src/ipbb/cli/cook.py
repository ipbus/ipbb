from __future__ import print_function, absolute_import


import click


# ------------------------------------------------------------------------------
@click.command('cook', short_help="Cook everything in the given recipe.")
@click.option('-q', '--quiet', 'aQuiet', is_flag=True, help='Suppress the output from the individual recipe commands.')
@click.pass_obj
@click.argument('recipe')
def cook(env, recipe, aQuiet):
    '''Cook everything in the given recipe'''
    from ..cmds.cook import cook
    cook(env, recipe, aQuiet)
