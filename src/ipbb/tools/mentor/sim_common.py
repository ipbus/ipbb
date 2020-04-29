from __future__ import print_function, absolute_import
# ------------------------------------------------------------------------------

import re
import sh

from itertools import izip

from ..common import which, OutputFormatter
from ..termui import *

_vsim = 'vsim'
_vcom = 'vcom'

# ------------------------------------------------
class ModelSimNotFoundError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ModelSimNotFoundError, self).__init__(message)


# --------------------------------------------------------------
def autodetect(executable=_vcom):

    """
    QuestaSim-64 vcom 10.6c_3 Compiler 2017.12 Dec 21 2017

    Model Technology ModelSim SE-64 vcom 10.6c Compiler 2017.07 Jul 25 2017
    """

    lVerExpr = r'(QuestaSim|ModelSim).+vcom\s(\d+\.\d+[\w]*).*\sCompiler'
    lVerRe = re.compile(lVerExpr, flags=re.IGNORECASE)

    if not which(executable):
        raise ModelSimNotFoundError(
            "'%s' not found in PATH. Failed to detect ModelSim/QuestaSim." % executable
        )

    lExe = sh.Command(executable)
    lVerStr = lExe('-version')

    m = lVerRe.search(str(lVerStr))

    if m is None:
        raise ModelSimNotFoundError("Failed to detect ModelSim/QuestaSim variant.")

    return m.groups()


# -------------------------------------------------------------------------
class ModelSimOutputFormatter(OutputFormatter):
    """Formatter for Vivado command line output

    Arguments:
        prefix (string): String to prepend to each line of output
    """

    def __init__(self, prefix=None, sep=' | ', quiet=False):
        super(ModelSimOutputFormatter, self).__init__(prefix, sep, quiet)

        self.pendingchars = ''
        self.skiplines = []

    def write(self, message):
        """Writes formatted message
        
        Args:
            message (string): Message to format
        """
        
        # put any pending character first
        msg = self.pendingchars + message
        # Flush pending chars
        self.pendingchars = ''

        # Splitting with regex, allows more flexibility
        lReNewLines = re.compile('(\r?\n)')

        # lines = msg.splitlines(True)
        lines = lReNewLines.split(msg)

        if not lines[-1]:
        # Drop the last entry if empty, i.e. the 
            lines.pop()
        else:
        # Otherwise queue it for the next round
            self.pendingchars = lines[-1]
            del lines[-1]


        assert (len(lines) % 2 == 0)

        # Iterate over pairs, line and newline match
        for lLine,lRet in izip(lines[::2], lines[1::2]):
            if lLine in self.skiplines:
                continue

            lColor = None
            if lLine.startswith('** Note:'):
                lColor = kBlue
            elif lLine.startswith('** Warning:'):
                lColor = kYellow
            elif lLine.startswith('** Error:'):
                lColor = kRed
            elif self.quiet:
                continue

            if lColor is not None:
                lLine = lColor + lLine + kReset

            self._write(self._prefixstr + lLine + lRet)
