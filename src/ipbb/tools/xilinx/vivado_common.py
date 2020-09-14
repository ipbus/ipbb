
import re
import sh


from ..common import which, OutputFormatter
from ..termui import *

# ------------------------------------------------
class VivadoNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(VivadoNotFoundError, self).__init__(message)
# ------------------------------------------------


# ------------------------------------------------
def _parseversion(verstr):
    """
Vivado:
    Vivado v2017.4 (64-bit)
    SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
    IP Build 2085800 on Fri Dec 15 22:25:07 MST 2017
    Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.

Vivado Lab:
    Vivado Lab Edition v2017.4 (64-bit)
    SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
    Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.

    """
    lVerExpr = r'(Vivado[\s\w]*)\sv(\d+\.\d)'

    lVerRe = re.compile(lVerExpr, flags=re.IGNORECASE)

    m = lVerRe.search(str(verstr))

    if m is None:
        raise VivadoNotFoundError("Failed to detect Vivado variant")

    return m.groups()
# ------------------------------------------------


# ------------------------------------------------
def autodetect(executable='vivado'):
    """
    Detects current vivado version
    """
    if not which(executable):
        raise VivadoNotFoundError("%s not found in PATH. Have you sourced Vivado\'s setup script?" % executable)

    lExe = sh.Command(executable)
    lVerStr = lExe('-version')
    return _parseversion(lVerStr)
# ------------------------------------------------


# -------------------------------------------------------------------------
class VivadoOutputFormatter(OutputFormatter):
    """Formatter for Vivado command line output

    Arguments:
        prefix (string): String to prepend to each line of output
    """
    def __init__(self, prefix=None, sep=' | ', quiet=False):
        super(VivadoOutputFormatter, self).__init__(prefix, sep, quiet)

        self.pendingchars = ''
        self.skiplines = ['\r\x1b[12C\r']

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
        for lLine,lRet in zip(lines[::2], lines[1::2]):
            if lLine in self.skiplines:
                continue

            lColor = None
            if lLine.startswith('INFO:'):
                lColor = kBlue
            elif lLine.startswith('WARNING:'):
                lColor = kYellow
            elif lLine.startswith('CRITICAL WARNING:'):
                lColor = kOrange
            elif lLine.startswith('ERROR:'):
                lColor = kRed
            elif self.quiet:
                continue

            if lColor is not None:
                lLine = lColor + lLine + kReset

            self._write(self._prefixstr + lLine + lRet)
# -------------------------------------------------------------------------
