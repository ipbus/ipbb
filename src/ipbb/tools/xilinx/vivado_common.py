
import re
import sh


from ...utils import which
from ..common import OutputFormatter
from ..termui import *

# ------------------------------------------------
class VivadoNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
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
    __log_all   = 0
    __log_info  = 10
    __log_warn  = 20
    __log_cwarn = 25
    __log_error = 30
    __log_fatal = 40
    __log_none  = 50

    __log_levels = {
        'all': __log_all,
        'info': __log_info,
        'warn': __log_warn,
        'cwarn': __log_cwarn,
        'error': __log_error,
        'fatal': __log_fatal,
        'none': __log_none,
    }

    def __init__(self, prefix=None, sep=' | ', loglevel='all'):
        super().__init__(prefix, sep, loglevel == 'none')

        self.pendingchars = ''
        self.skiplines = ['\r\x1b[12C\r']
        self.loglevel = self.__log_levels[loglevel]

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

            if self.quiet:
                continue

            if self.loglevel == self.__log_none:
                continue
            
            lColor = None

            if lLine.startswith('INFO:'):
                if self.loglevel <= self.__log_info:
                    lColor = kBlue
                else:
                    continue
            elif lLine.startswith('WARNING:'):
                if self.loglevel <= self.__log_warn:
                    lColor = kYellow                
                else:
                    continue
            elif lLine.startswith('CRITICAL WARNING:'):
                if self.loglevel <= self.__log_cwarn:
                    lColor = kOrange
                else:
                    continue
            elif lLine.startswith('ERROR:'):
                if self.loglevel <= self.__log_fatal:
                    lColor = kRed
                else:
                    continue
            elif lLine.startswith('FATAL:'):
                if self.loglevel <= self.__log_fatal:
                    lColor = kMagenta
                else:
                    continue
            else:
                if self.loglevel >= self.__log_info:
                    continue


            if lColor is not None:
                lLine = lColor + lLine + kReset

            self._write(self._prefixstr + lLine + lRet)
# -------------------------------------------------------------------------
