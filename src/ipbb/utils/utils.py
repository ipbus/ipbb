# NOTE TO SELF: Merge with tools/common.py

import csv
import pathlib
import platform
import os
import ipaddress
import sys
import re

from click import get_current_context, ClickException, Abort, BadParameter
from os.path import join, relpath, exists, split, realpath
from rich.prompt import Confirm
from rich.table import Table
from typing import NoReturn

from locale import getpreferredencoding

from ..console import cprint, console

DEFAULT_ENCODING = getpreferredencoding() or "UTF-8"

# ------------------------------------------------------------------------------
def read_os_release():
    """Check OS, and on Linux return a dictionary with /etc/os-release info

    On any platform other than Linux, None is returned.

    """

    res = None
    if platform.system() == 'Linux':
        in_file_name = pathlib.Path("/etc/os-release")
        with open(in_file_name) as in_stream:
            non_empty_lines = (l for l in in_stream if not l.isspace())
            reader = csv.reader(non_empty_lines, delimiter="=")
            res = dict(reader)

    return res
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class DirSentry:
    """
    Helper class implementing the guard pattern for temporary directory switches.
    
    Attributes:
        dir (string): Destination directory
    """
    def __init__(self, aDir):
        self.dir = aDir

    def __enter__(self):
        if not exists(self.dir):
            raise RuntimeError('Directory ' + self.dir + ' does not exist')

        self._lOldDir = realpath(os.getcwd())
        os.chdir(self.dir)
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self._lOldDir)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class SmartOpen(object):

    # -------------------------------------------
    def __init__(self, aTarget):
        if isinstance(aTarget, str):
            self.target = open(aTarget, 'w')
        elif aTarget is None:
            self.target = sys.stdout
        else:
            self.target = aTarget

    # -------------------------------------------
    @property
    def path(self):
        if self.target is not sys.stdout:
            return self.target.name
        else:
            return None

    # -------------------------------------------
    def __enter__(self):
        return self

    # -------------------------------------------
    def __exit__(self, type, value, traceback):
        if self.target is not sys.stdout:
            self.target.close()

    # -------------------------------------------
    def __call__(self, *strings):
        self.target.write(' '.join(strings))
        self.target.write("\n")
        self.target.flush()

    # -------------------------------------------


# ------------------------------------------------------------------------------
# Helper function equivalent to which in posix systems
def which(aExecutable):
    '''Searches for exectable il $PATH'''
    lSearchPaths = (
        os.environ["PATH"].split(os.pathsep)
        if aExecutable[0] != os.sep
        else [os.path.dirname(aExecutable)]
    )
    for lPath in lSearchPaths:
        if not os.access(os.path.join(lPath, aExecutable), os.X_OK):
            continue
        return os.path.normpath(os.path.join(lPath, aExecutable))
    return None


# ------------------------------------------------------------------------------
def mkdir(path, mode=0o777):
    try:
        os.makedirs(path, mode)
    except OSError:
        if os.path.exists(path) and os.path.isdir(path):
            return
        raise



# ------------------------------------------------------------------------------
def findFirstParentDir(aDirPath, aParentDir='/'):
    if not aDirPath.startswith(aParentDir):
        raise RuntimeError("{} is not a parent folder of {}".format(aParentDir, aDirPath))

    lDirPath = aDirPath
    while lDirPath != aParentDir:
        if exists(lDirPath):
            return lDirPath
        lDirPath, _ = split(lDirPath)
    return aParentDir

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def findFileDirInParents(aFileName : str, aDirPath : str) -> str:
    """
    Find, in the current directory tree, the folder in which a given file is located.
    
    Args:
        aFileName (str): Name of the file to search
        aDirPath (str): Search path
    
    Returns:
        str: Description
    """
    lDirPath = aDirPath
    while lDirPath != '/':
        lBuildFile = join(lDirPath, aFileName)
        if exists(lBuildFile):
            return lDirPath
        lDirPath, _ = split(lDirPath)

    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def findFileInParents(aFileName : str, aDirPath : str=os.getcwd()) -> str:
    """
    Find a file of given name, in the current directory tree branch,
    starting from dirpat and moving upwards
    
    Args:
        aFileName (str): Filename to find
        aDirPath (str, optional): Search path
    
    Returns:
        str: Path to the file
    """

    lDirPath = findFileDirInParents(aFileName, aDirPath)

    return join(lDirPath, aFileName) if lDirPath is not None else None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def ensureNoParsingErrors(aCurrentProj, aDepFileParser) -> NoReturn:
    """
    Throwns an exception if dep parsing errors are detected.

    Args:
        aCurrentProj (TYPE): Description
        aDepFileParser (TYPE): Description
    
    Returns:
        NoReturn: nothing
    
    Raises:
        Abort: Description
    """
    from ..depparser import DepFormatter

    if not aDepFileParser.errors:
        return

    fmt = DepFormatter(aDepFileParser)
    cprint("ERROR: Project '{}' contains {} parsing error{}.".format(
        aCurrentProj,
        len(aDepFileParser.errors),
        ("" if len(aDepFileParser.errors) == 1 else "s"),
    ), style='red')
    cprint(fmt.draw_parsing_errors(), style='red')

    raise Abort()

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def ensureNoMissingFiles(aCurrentProj, aDepFileParser):
    """
    Check the dependency file tree for unresolved files.
    If detected, ask the user for confirmation to continue
    """

    from ..depparser import DepFormatter

    if not aDepFileParser.unresolved:
        return

    fmt = DepFormatter(aDepFileParser)
    cprint("ERROR: Project '{}' contains unresolved dependencies: {} unresolved file{}.".format(
        aCurrentProj,
        len(aDepFileParser.unresolved),
        ("" if len(aDepFileParser.unresolved) == 1 else "s"),
    ), style='red')
    cprint(fmt.draw_unresolved_files(), style='red')

    cprint("")
    if not Confirm.ask("Do you want to continue anyway?"):
        raise Abort()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def logVivadoConsoleError( aExc ):
    console.log("Vivado error/critical warnings detected", style='red')
    console.log("\n".join(aExc.errors), markup=False, style='red')
    console.log("\n".join(aExc.criticalWarns), markup=False, style='yellow')    


# ------------------------------------------------------------------------------

