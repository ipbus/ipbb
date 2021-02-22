
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
def cleanup(ictx):

    _, lSubdirs, lFiles = next(os.walk(ictx.currentproj.path))
    for f in [kProjAreaFile, kProjUserFile]:
        if f not in lFiles:
            continue

        lFiles.remove(f)

    if lFiles and not click.confirm(
        style(
            "All files and directories in\n'{}'\n will be deleted.\nDo you want to continue?".format(
                ictx.currentproj.path
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
def user_config(ictx, aList, aAdd, aUnset):

    echo("User settings")

    if aAdd:
        lKey, lValue = aAdd
        ictx.currentproj.usersettings[lKey] = lValue
        ictx.currentproj.saveUserSettings()

    if aUnset:
        del ictx.currentproj.usersettings[aUnset]
        ictx.currentproj.saveUserSettings()

    if ictx.currentproj.usersettings:
        echo(formatDictTable(ictx.currentproj.usersettings))


# ------------------------------------------------------------------------------
def addrtab(ictx, aDest):
    '''Copy address table files into addrtab subfolder'''

    try:
        os.mkdir(aDest)
    except OSError:
        pass

    import sh

    if not ictx.depParser.commands["addrtab"]:
        secho(
            "\nWARNING no address table files defined in {}.\n".format(
                ictx.currentproj.name
            ),
            fg='yellow',
        )
        return

    for addrtab in ictx.depParser.commands["addrtab"]:
        print(sh.cp('-avL', addrtab.filepath, join(aDest, basename(addrtab.filepath))))
    secho(
        "\n{}: Address table files collected in '{}'.\n".format(
            ictx.currentproj.name, aDest
        ),
        fg='green',
    )
