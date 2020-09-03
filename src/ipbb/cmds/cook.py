from __future__ import print_function, absolute_import

# import os
import sh
# import sys
import click

from click import echo, secho, style, confirm
# from os.path import join, split, exists, abspath, splitext, relpath, basename
# from ..defaults import kProjAreaFile, kProjUserFile
# from ._utils import DirSentry, formatDictTable
# from ..tools.common import which


# ------------------------------------------------------------------------------
def cook(env, aRecipe, aQuiet):
    '''Cook everything in the given recipe'''

    try:
        with open(aRecipe, 'r') as in_file:
            recipe = in_file.readlines()
    except Exception as err:
        secho(
            "\nERROR Failed to read recipe: {}.\n".format(
                str(err)
            ),
            fg='red'
        )
        return

    # Strip lines, just in case, and remove comments and empty lines.
    lines = [i.strip() for i in recipe]
    lines = [i for i in lines if not i.startswith("#")]
    lines = [i for i in lines if len(i)]

    for line in lines:
        secho(
            "Executing\n  '{}'".format(
                line
            ),
            fg='green'
        )
        pieces = line.split()
        try:
            cmd_name = pieces[0]
            cmd = getattr(sh, cmd_name)
            args = None if len(pieces) == 1 else pieces[1:]
            # There is no real use running with '_iter' unless we want
            # to follow the output.
            run_with_iter = not aQuiet
            # NOTE: Have to avoid using the _iter keyword on built-in
            # commands (i.e., those starting with 'b_').
            run_with_iter = run_with_iter and not cmd.__name__.startswith('b_')
            if run_with_iter:
                for output_line in cmd(*args, _iter=True):
                    secho(output_line, fg='green')
            else:
                cmd(*args)
        except Exception as err:
            secho(
                "\nERROR Failed to execute '{}': {}.\n".format(
                    line, str(err)
                ),
                fg='red'
            )
            break
