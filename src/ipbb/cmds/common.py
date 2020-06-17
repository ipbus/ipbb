from __future__ import print_function, absolute_import

import os
import sh
import sys
import click

from click import echo, secho, style, confirm
from os.path import join, split, exists, abspath, splitext, relpath, basename
from ..defaults import kProjAreaFile, kProjUserFile
from ._utils import DirSentry, formatDictTable
from ..tools.common import which


# ------------------------------------------------------------------------------
def cleanup(env):

    _, lSubdirs, lFiles = next(os.walk(env.currentproj.path))
    for f in [kProjAreaFile, kProjUserFile]:
        if f not in lFiles:
            continue

        lFiles.remove(f)

    if lFiles and not click.confirm(
        style(
            "All files and directories in\n'{}'\n will be deleted.\nDo you want to continue?".format(
                env.currentproj.path
            ),
            fg='yellow',
        )
    ):
        return

    if lSubdirs:
        sh.rm('-rv', *lSubdirs, _out=sys.stdout)

    if lFiles:
        sh.rm('-v', *lFiles, _out=sys.stdout)


# ------------------------------------------------------------------------------
def user_config(env, aList, aAdd, aUnset):

    echo("User settings")

    if aAdd:
        lKey, lValue = aAdd
        env.currentproj.usersettings[lKey] = lValue
        env.currentproj.saveUserSettings()

    if aUnset:
        del env.currentproj.usersettings[aUnset]
        env.currentproj.saveUserSettings()

    if env.currentproj.usersettings:
        echo(formatDictTable(env.currentproj.usersettings))


# ------------------------------------------------------------------------------
def addrtab(env, aDest):
    '''Copy address table files into addrtab subfolder'''

    try:
        os.mkdir(aDest)
    except OSError:
        pass

    import sh

    if not env.depParser.commands["addrtab"]:
        secho(
            "\nWARNING no address table files defined in {}.\n".format(
                env.currentproj.name
            ),
            fg='yellow',
        )
        return

    for addrtab in env.depParser.commands["addrtab"]:
        print(sh.cp('-av', addrtab.filepath, join(aDest, basename(addrtab.filepath))))
    secho(
        "\n{}: Address table files collected in '{}'.\n".format(
            env.currentproj.name, aDest
        ),
        fg='green',
    )
