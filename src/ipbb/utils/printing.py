from rich.table import Table
from typing import NoReturn

from ..tools.alien import AlienBranch
from ..console import cprint, console

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
        lAlienTable.add_row( str(k), aFmtr(v) if aFmtr else str(v))

    return lAlienTable
