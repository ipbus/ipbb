from typing import NoReturn

from ..tools.alien import AlienBranch
from ..console import cprint, console
from rich.table import Table
from rich.panel import Panel
from rich.style import Style


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


# ------------------------------------------------------------------------------
def notice_panel(message: str, title: str, color: str):

    cprint(Panel(f"{message}", title=title, style=Style(color=color, italic=True)))

# ------------------------------------------------------------------------------
def deprecation_warning( message: str ):

    notice_panel(f"{message}", title="DEPRECATION WARNING", color="yellow")


# ------------------------------------------------------------------------------
def warning_notice( message: str ):

    notice_panel(f"{message}", title="WARNING", color="yellow")

# ------------------------------------------------------------------------------
def error_notice( message: str ):

    notice_panel(f"{message}", title="ERROR", color="red")

if __name__ == '__main__':
    deprecation_warning("Deprecation warning example")
    error_notice("Error notification example")