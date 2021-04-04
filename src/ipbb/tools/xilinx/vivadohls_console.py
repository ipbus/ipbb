
# Modules
import logging
import pexpect
import sys
import re
import collections
import subprocess
import os.path
import atexit
import sh
import tempfile
import psutil

# Elements
from os.path import join, split, exists, splitext, basename
from click import style
from ..common import which, OutputFormatter
from ..termui import *
from ..tcl_console import consolectxmanager, TCLConsoleSnoozer
from ..common import DEFAULT_ENCODING

kHLSLogDebug = False


# ------------------------------------------------
class VivadoHLSNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
# ------------------------------------------------


# ------------------------------------------------
def _parseversion(verstr):
    """
Vivado(TM) HLS - High-Level Synthesis from C, C++ and SystemC v2018.3 (64-bit)
SW Build 2405991 on Thu Dec  6 23:36:41 MST 2018
IP Build 2404404 on Fri Dec  7 01:43:56 MST 2018
Copyright 1986-2018 Xilinx, Inc. All Rights Reserved.
    """
    lVerExpr = r'(Vivado\(TM\)[\s\w]*)\s-.*v(\d+\.\d)'

    lVerRe = re.compile(lVerExpr, flags=re.IGNORECASE)

    m = lVerRe.search(str(verstr))

    if m is None:
        raise VivadoHLSNotFoundError("Failed to detect VivadoHLS variant")

    return m.groups()
# ------------------------------------------------


# ------------------------------------------------
def autodetecthls(executable='vivado_hls'):
    """

    """


    if not which(executable):
        raise VivadoHLSNotFoundError("%s not found in PATH. Have you sourced Vivado\'s setup script?" % executable)

    lExe = sh.Command(executable)
    lVerStr = lExe('-version')
    return _parseversion(lVerStr)
# ------------------------------------------------


# -------------------------------------------------------------------------
class VivadoHLSOutputFormatter(OutputFormatter):
    """Formatter for Vivado command line output

    Arguments:
        prefix (string): String to prepend to each line of output
    """
    def __init__(self, prefix=None, sep=' | ', quiet=False):
        super().__init__(prefix, sep, quiet)

        self.pendingchars = ''
        self.skiplines = [r'\r\x1b[12C\r']

    def write(self, message):
        """Writes formatted message
        
        Args:
            message (string): Message to format
        """
        
        # TODELETE
        if kHLSLogDebug:
            print(kCyan+'raw in  >> '+kReset+repr(message))
            if self.pendingchars:
                print(kCyan+'raw pen >> '+kReset+repr(self.pendingchars))

        # put any pending character first
        msg = self.pendingchars + message
        # Flush pending chars
        self.pendingchars = ''

        # Splitting with regex, allows more flexibility
        lReNewLines = re.compile('(\r?\n)')

        # lines = msg.splitlines(True)
        lines = lReNewLines.split(msg)

        # TODELETE
        if kHLSLogDebug:
            print(kRed+'split   >> '+kReset+repr(lines))

        if not lines[-1]:
        # Drop the last entry if empty, i.e. the 
            lines.pop()
        else:
        # Otherwise queue it for the next round
            self.pendingchars = lines[-1]
            del lines[-1]


        assert (len(lines) % 2 == 0)
        # TODELETE
        if kHLSLogDebug:
            print(kRed+'c split >> '+kReset+repr(lines))

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

            if kHLSLogDebug:
                self._write(kBlue+"fmtxout >> "+kReset+repr(self._prefixstr + lLine + lRet) + '\n')
            self._write(self._prefixstr + lLine + lRet)
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
class VivadoHLSConsoleError(Exception):
    """Exception raised for errors in the input.
    
    Attributes:
        command (list): input command in which the error occurred
        errors (list): Error messages
        criticalWarns (list): Critical warning messages
    """

    def __init__(self, command, errors, criticalWarns=None):

        self.errors = errors
        self.criticalWarns = criticalWarns
        self.command = command

    def __str__(self):
        return self.__class__.__name__ + '(\'{}\', errors: {}, critical warnings {})'.format(self.command, len(self.errors), len(self.criticalWarns))
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
class VivadoHLSConsole(object):
    """Class to interface to Vivado TCL console
    
    Attributes:
        variant (str): Vivado variant
        version (str): Vivado version
        isAlive (bool): Status of the vivado process
    
    """

    __reCharBackspace = re.compile(r'.\x08')
    __reError = re.compile(r'^ERROR:')
    __reCriticalWarning = re.compile(r'^CRITICAL WARNING:')
    __instances = set()
    __promptMap = {
        'vivado_hls': re.compile(r'\x1b\[2K\r\rvivado_hls>\s'),
    }
    __newlines = [u'\r\n']
    __cmdSentAck = '\r\x1b[12C\r'

    # --------------------------------------------------------------
    @classmethod
    def killAllInstances(cls):
        lInstances = set(cls.__instances)
        for lInstance in lInstances:
            lInstance.close()
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    @property
    def quiet(self):
        return self._out.quiet

    @quiet.setter
    def quiet(self, value):
        self._out.quiet = value
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    @property
    def processinfo(self):
        return self._processinfo

    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __init__(self, executable='vivado_hls', prompt=None, stopOnCWarnings=False, echo=True, showbanner=False, sid=None, loglabel=None ):
        """
        Args:
            sessionid (str): Name of the VivadoHLS session
            echo (bool): Switch to enable echo messages
            echoprefix (str): Prefix to echo message
            executable (str): Executable name
            prompt (str):
            stopOnCWarnings (bool): Stop on Critical Warnings
        """
        super().__init__()

        # Set up logger first
        self._log = logging.getLogger('VivadoHLS')
        self._log.debug('Starting VivadoHLS')

        self._stopOnCWarnings = stopOnCWarnings
        # define what executable to run
        self._executable = executable
        if not which(self._executable):
            raise VivadoHLSNotFoundError(self._executable + " not found in PATH. Have you sourced VivadoHLS\'s setup script?")

        # Define the prompt to use
        if prompt is None:
            # set prompt pattern based on sim variant
            self._prompt = self.__promptMap[executable]
        else:
            self._prompt = prompt

        # Set up the output formatter
        self._out = VivadoHLSOutputFormatter(
            sid, quiet=(not echo)
        )

        self._out.write('\n' + '- Starting VivadoHLS -'+'-' * 40 + '\n')
        self._out.quiet = (not showbanner)
       
        loglabel = loglabel if loglabel else sid
        lLogName = self._executable + (('_' + loglabel) if loglabel else '')
        self._process = pexpect.spawn(self._executable, [
                '-i', 
                '-l', lLogName+'.log',
            ],
            echo=echo,
            logfile=self._out,
            encoding=DEFAULT_ENCODING,
            # preexec_fn=on_parent_exit('SIGTERM')
        )
        
        # Compile the list of patterns to detect the prompt
        self._rePrompt = self._process.compile_pattern_list(
            self.__newlines+[self._prompt, pexpect.TIMEOUT]
        )

        # Set send delay
        self._process.delaybeforesend = 0.00  # 1

        # Wait for vivadoHLS to wake up
        startupstr = self.__expectPrompt()

        # Extract version infomation
        self._variant, self._version = _parseversion(''.join(startupstr[0]))
        self._out.quiet = (not echo)
        self._log.debug('VivadoHLS up and running')
        self._out.write('\n' + '- Started {} {} -'.format(self.variant, self.version)+'-' * 40 + '\n')

        # Create a process descriptor
        self._processinfo = psutil.Process(self._process.pid)
        # Method mapping
        self.isAlive = self._process.isalive
        # Add self to the list of instances
        self.__instances.add(self)

    # --------------------------------------------------------------
    @property
    def variant(self):
        return self._variant
    
    # --------------------------------------------------------------
    @property
    def version(self):
        return self._version
    
    # --------------------------------------------------------------
    def __del__(self):
        self.close()

    # --------------------------------------------------------------
    def __call__(self, aCmd='', aMaxLen=1):
        return self.execute(aCmd, aMaxLen)

    # --------------------------------------------------------------
    def __checkEcho(self, aText, aBefore):
        """
        Hard check: First line of output must match the injected command
        """
        lRcvd = aBefore
        lXpctd = self.__cmdSentAck
        # if kHLSLogDebug:
        #     print(kYellow+'send ack>> '+kReset+repr(aBefore))
        if lRcvd != lXpctd:
            # --------------------------------------------------------------
            print('-' * 20)
            print('Echo character-by-character diff')
            # Find where the 2 strings don't match
            print('sent:', len(lXpctd), 'rcvd', len(lRcvd))

            # find the first mismatching character
            minlen = min(len(lRcvd), len(lXpctd))
            maxlen = max(len(lRcvd), len(lXpctd))
            x = next((i for i in range(minlen) if lRcvd[i] != lXpctd[i]), minlen)

            a = x - 10
            b = x + 10
            for i in range(max(a, 0), min(b, maxlen)):
                r = lRcvd[i] if len(lRcvd) > i else ' '
                s = lXpctd[i] if len(lXpctd) > i else ' '
                # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s),
                # ord(s) > 128
                print(i, '\t', repr(s), repr(r), r == s, ord(r))

            print(''.join([str(i % 10) for i in range(len(lRcvd))]))
            print(lRcvd)
            print(''.join([str(i % 10) for i in range(len(lXpctd))]))
            print(lXpctd)
            # --------------------------------------------------------------
            raise RuntimeError(
                "Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(
                    lXpctd, lRcvd
                )
            )

    # --------------------------------------------------------------
    def __send(self, aText):

        x = self._process.sendline(aText)
        lIndex = self._process.expect(self.__newlines)

        # --------------------------------------------------------------
        # Hard check: First line of output must match the injected command
        self.__checkEcho(aText, self._process.before)

    # --------------------------------------------------------------
    def __expectPrompt(self, aMaxLen=100):
        lIndex = None
        lBuffer = collections.deque([], aMaxLen)
        lErrors = []
        lCriticalWarnings = []

        # --------------------------------------------------------------
        lTimeoutCounts = 0
        while True:
            # Search for newlines, prompt, end-of-file
            lIndex = self._process.expect_list(self._rePrompt)
            # if kHLSLogDebug:
            #     print(kGreen+"expect  >> "+kReset,lIndex, repr(self._process.before))

            # ----------------------------------------------------------
            # Break if prompt
            if lIndex == 1:
                if not lBuffer:
                    lBuffer.append(None)
                break
            elif lIndex == 2:
                lTimeoutCounts += 1
                print ("VivadoHLSConsole >> Time since last command: {0}s".format(
                    lTimeoutCounts * self._process.timeout))
            # ----------------------------------------------------------

            lBefore = str(self._process.before)
            # Store the output in the circular buffer
            lBuffer.append(lBefore)

            if self.__reError.match(lBefore):
                lErrors.append(lBefore)
            elif self.__reCriticalWarning.match(lBefore):
                lCriticalWarnings.append(lBefore)

        # --------------------------------------------------------------

        return lBuffer, lErrors, lCriticalWarnings

    # --------------------------------------------------------------
    def close(self):

        # Return immediately of already dead
        if not hasattr(self, '_process') or not self._process.isalive():
            self._log.debug('VivadoHLS has already been stopped')
            # try:
            #   # I am being pedantic here, in case, for any reason, it wasn't done yet
            #   self.__instances.remove(self)
            # except KeyError:
            #   pass
            return

        self._log.debug('Shutting VivadoHLS down')
        try:
            self.__send('quit')
        except pexpect.ExceptionPexpect:
            pass

        # Write one last newline
        self._out.write('- Terminating VivadoHLS (pid {}) -'.format(self._process.pid)+'-' * 40 + '\n')
        # Just in case
        self._process.terminate(True)

        # Remove self from the list of instances
        self.__instances.remove(self)

    # --------------------------------------------------------------
    @property
    def echoprefix(self):
        return self._out.prefix

    # --------------------------------------------------------------
    @echoprefix.setter
    def echoprefix(self, prefix):
        self._out.prefix = prefix

    # --------------------------------------------------------------
    def execute(self, aCmd, aMaxLen=1):
        if not isinstance(aCmd, str):
            raise TypeError('expected string, found '+str(type(aCmd)))

        if aCmd.count('\n') != 0:
            raise ValueError('Format error. Newline not allowed in commands')

        self.__send(aCmd)
        lBuffer, lErrors, lCriticalWarnings = self.__expectPrompt(aMaxLen)

        if lErrors or (self._stopOnCWarnings and lCriticalWarnings):
            raise VivadoHLSConsoleError(aCmd, lErrors, lCriticalWarnings)

        return tuple(lBuffer)

    # --------------------------------------------------------------
    def executeMany(self, aCmds, aMaxLen=1):
        if not isinstance(aCmds, list):
            raise TypeError('expected list')

        lOutput = []
        for lCmd in aCmds:
            lOutput.extend(self.execute(lCmd, aMaxLen))
        return lOutput

    # --------------------------------------------------------------
    def changeMsgSeverity(self, aIds, aSeverity):
        """Change the severity of a single/multiple messages
        
        Args:
            aIds (str or list): List of message ids to update
            aSeverity (str): Target severity
        """
        lIds = aIds if isinstance(aIds, list) else [aIds]
        self.executeMany(['set_msg_config -id {{{}}} -new_severity {{{}}}'.format(i, aSeverity) for i in lIds])


# -------------------------------------------------------------------------
@consolectxmanager
class VivadoHLSSession(VivadoHLSConsole):
    pass

VivadoHLSSnoozer = TCLConsoleSnoozer

@atexit.register
def __goodbye():
    VivadoHLSConsole.killAllInstances()
# -------------------------------------------------------------------------
