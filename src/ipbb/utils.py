
import os
import ipaddress
import sys
import re

from click import get_current_context, ClickException, Abort, BadParameter
from os.path import join, relpath, exists, split, realpath
from rich.prompt import Confirm
from rich.table import Table

from .tools.alien import AlienBranch
from .console import cprint, console
from .depparser import DepFormatter

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
def raiseError(aMessage):
    """
    Print the error message to screen in bright red and a ClickException error
    """

    cprint("\nERROR: " + aMessage + "\n", style='red')
    raise ClickException("Command aborted.")

# ------------------------------------------------------------------------------


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
def findFileDirInParents(aFileName, aDirPath):
    """
    Find, in the current directory tree, the folder in which a given file is located.

    Args:
        aFileName (str): Name of the file to search
        aDirPath (str, optional): Search path

    Returns:
        TYPE: Description
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
def findFileInParents(aFileName, aDirPath=os.getcwd()):
    """
    Find a file of given name, in the current directory tree branch,
    starting from dirpat and moving upwards
    """

    lDirPath = findFileDirInParents(aFileName, aDirPath)

    return join(lDirPath, aFileName) if lDirPath is not None else None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def ensureNoParsingErrors(aCurrentProj, aDepFileParser):
    """
    { item_description }
    """
    if not aDepFileParser.errors:
        return

    fmt = DepFormatter(aDepFileParser)
    cprint("ERROR: Project '{}' contains {} parsing error{}.".format(
        aCurrentProj,
        len(aDepFileParser.errors),
        ("" if len(aDepFileParser.errors) == 1 else "s"),
    ), style='red')
    cprint(fmt.drawParsingErrors(), style='red')

    raise Abort()

# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
def ensureNoMissingFiles(aCurrentProj, aDepFileParser):
    """
    Check the dependency file tree for unresolved files.
    If detected, ask the user for confirmation to continue
    """

    if not aDepFileParser.unresolved:
        return

    fmt = DepFormatter(aDepFileParser)
    cprint("ERROR: Project '{}' contains unresolved dependencies: {} unresolved file{}.".format(
        aCurrentProj,
        len(aDepFileParser.unresolved),
        ("" if len(aDepFileParser.unresolved) == 1 else "s"),
    ), style='red')
    cprint(fmt.drawUnresolvedFiles(), style='red')

    cprint("")
    if not Confirm.ask("Do you want to continue anyway?"):
        raise click.Abort()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def logVivadoConsoleError( aExc ):
    console.log("Vivado error/critical warnings detected", style='red')
    console.log("\n".join(aExc.errors), markup=False, style='red')
    console.log("\n".join(aExc.criticalWarns), markup=False, style='yellow')    


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def validateComponent(ctx, param, value):
    lTopSeps = value.count(':')
    lPathSeps = value.count(os.path.sep)
    # Validate the format
    if not ((lTopSeps == 1) or (lTopSeps == 0 and lPathSeps == 0)):
        raise BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

    return tuple(value.split(':'))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def validateMultiplePackageOrComponents(ctx, param, value):
    pocs = []
    for v in value:
        lSeparators = v.count(':')
        # Validate the format
        if lSeparators > 1:
            raise BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

        pocs.append(tuple(v.split(':')))

    return tuple(pocs)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def validateIpAddress(value):
    if value is None:
        return

    try:
        lIp = ipaddress.ip_address(value)
    except ValueError as lExc:
        # raise_with_traceback(BadParameter(str(lExc)), sys.exc_info()[2])
        tb = sys.exc_info()[2]
        raise BadParameter(str(lExc)).with_traceback(tb)

    lHexIp = ''.join([ '%02x' % ord(c) for c in lIp.packed])

    return 'X"{}"'.format(lHexIp)


# ------------------------------------------------------------------------------
def validateMacAddress(value):

    if value is None:
        return

    m = re.match(r'([0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})', value)
    if m is None:
        raise BadParameter('Malformed mac address : %s' % value)

    lHexMac = ''.join([ '%02x' % int(c, 16) for c in value.split(':')])
    return 'X"{}"'.format(lHexMac)


# ------------------------------------------------------------------------------
def printRegTable(aRegs, aHeader=True, aSort=True):
    cprint ( formatRegTable(aRegs, aHeader, aSort) )


# ------------------------------------------------------------------------------
def formatRegTable(aRegs, aHeader=True, aSort=True):

    lRegTable = Table('name', 'value', show_header=aHeader)
    for k in (sorted(aRegs) if aSort else aRegs):
        lRegTable.add_row( str(k), hex(aRegs[k]) )
    return lRegTable


# ------------------------------------------------------------------------------
def printDictTable(aDict, aHeader=True, aSort=True, aFmtr=None):
    cprint ( formatDictTable(aDict, aHeader, aSort, aFmtr) )


# ------------------------------------------------------------------------------
def formatDictTable(aDict, aHeader=True, aSort=True, aFmtr=str):

    lDictTable = Table('name', 'value', show_header=aHeader)
    for k in (sorted(aDict) if aSort else aDict):
        v = aDict[k]
        lDictTable.add_row(str(k), aFmtr(v) if aFmtr else v)
    return lDictTable


# ------------------------------------------------------------------------------
def printAlienTable(aBranch, aHeader=True, aSort=True, aFmtr=None):
    cprint ( formatAlienTable(aBranch, aHeader, aSort, aFmtr) )


# ------------------------------------------------------------------------------
def formatAlienTable(aBranch, aHeader=True, aSort=True, aFmtr=str):
    lAlienTable = Table('name', 'value', show_header=aHeader)

    for k in (sorted(aBranch) if aSort else aBranch):
        v = aBranch[k]
        if isinstance(v, AlienBranch):
            continue
        lAlienTable.add_row( str(k), aFmtr(v) if aFmtr else v)

    return lAlienTable



# ------------------------------------------------------------------------------
def getClickRootName():
    return get_current_context().find_root().info_name


