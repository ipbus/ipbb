
import os
import sh
import sys
import click

from rich.prompt import Confirm
from rich.text import Text
from os.path import join, split, exists, abspath, splitext, relpath, basename

from ..console import cprint, console
from ..defaults import kProjAreaFile, kProjUserFile
from ..utils import DirSentry, formatDictTable
from ..utils import which


# ------------------------------------------------------------------------------
def cleanup(ictx):

    _, lSubdirs, lFiles = next(os.walk(ictx.currentproj.path))
    for f in [kProjAreaFile, kProjUserFile]:
        if f not in lFiles:
            continue

        lFiles.remove(f)

    if lFiles and not Confirm.ask(
            Text(f"All files and directories in\n'{ictx.currentproj.path}'\n will be deleted.\nDo you want to continue?",
            style='yellow')
    ):
        return

    if lSubdirs:
        sh.rm('-rv', *lSubdirs, _out=sys.stdout)

    if lFiles:
        sh.rm('-v', *lFiles, _out=sys.stdout)


# ------------------------------------------------------------------------------
def user_config(ictx, aList, aAdd, aUnset):

    cprint("User settings")

    if aAdd:
        lKey, lValue = aAdd
        ictx.currentproj.usersettings[lKey] = lValue
        ictx.currentproj.saveUserSettings()

    if aUnset:
        del ictx.currentproj.usersettings[aUnset]
        ictx.currentproj.saveUserSettings()

    if ictx.currentproj.usersettings:
        cprint(formatDictTable(ictx.currentproj.usersettings))


# ------------------------------------------------------------------------------
def addrtab(ictx, aDest):
    '''Copy address table files into addrtab subfolder'''

    try:
        os.mkdir(aDest)
    except OSError:
        pass

    if not ictx.depParser.commands["addrtab"]:
        cprint(
            f"\nWARNING no address table files defined in {ictx.currentproj.name}.\n",
            style='yellow',
        )
        return

    for addrtab in ictx.depParser.commands["addrtab"]:
        cprint(sh.cp('-avL', addrtab.filepath, join(aDest, basename(addrtab.filepath))))
    
    console.log(
        f"{ictx.currentproj.name}: Address table files collected in '{aDest}'.",
        style='green',
    )
