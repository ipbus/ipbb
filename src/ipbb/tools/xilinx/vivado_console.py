from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------


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
from itertools import izip
from ..common import which, OutputFormatter
from ..termui import *
from .tcl_console import lazyctxmanager, TCLConsoleSnoozer

# ------------------------------------------------
# This is for when python 2.7 will become available
# pexpect.spawn(...,preexec_fn=on_parent_exit('SIGTERM'))
import signal
from ctypes import cdll


# Constant taken from http://linux.die.net/include/linux/prctl.h
PR_SET_PDEATHSIG = 1


class PrCtlError(Exception):
    pass


def on_parent_exit(signame):
    """
    Return a function to be run in a child process which will trigger
    SIGNAME to be sent when the parent process dies
    """
    signum = getattr(signal, signame)

    def set_parent_exit_signal():
        # http://linux.die.net/man/2/prctl
        result = cdll['libc.so.6'].prctl(PR_SET_PDEATHSIG, signum)
        if result != 0:
            raise PrCtlError('prctl failed with error code %s' % result)
    return set_parent_exit_signal
# ------------------------------------------------


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
    def __init__(self, prefix=None, quiet=False):
        super(VivadoOutputFormatter, self).__init__(prefix, quiet)

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
        for lLine,lRet in izip(lines[::2], lines[1::2]):
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

            self._write((self.prefix if self.prefix else '') + lLine + lRet)
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
class VivadoConsoleError(Exception):
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
class VivadoConsole(object):
    """Class to interface to Vivado TCL console
    
    Attributes:
        variant (str): Vivado variant
        version (str): Vivado version
        isAlive (bool): Status of the vivado process
    
    """

    __reCharBackspace = re.compile(u'.\x08')
    __reError = re.compile(u'^ERROR:')
    __reCriticalWarning = re.compile(u'^CRITICAL WARNING:')
    __instances = set()
    __promptMap = {
        'vivado': u'Vivado%\s',
        'vivado_lab': u'vivado_lab%\s'
    }
    __newlines = [u'\r\n']

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
    def __init__(self, sessionid=None, echo=True, echobanner=False, echoprefix=None, executable='vivado', prompt=None, stopOnCWarnings=False):
        """
        Args:
            sessionid (str): Name of the Vivado session
            echo (bool): Switch to enable echo messages
            echoprefix (str): Prefix to echo message
            executable (str): Executable name
            prompt (str):
            stopOnCWarnings (bool): Stop on Critical Warnings
        """
        super(VivadoConsole, self).__init__()

        # Set up logger first
        self._log = logging.getLogger('Vivado')
        self._log.debug('Starting Vivado')

        self._stopOnCWarnings = stopOnCWarnings
        # define what executable to run
        self._executable = executable
        if not which(self._executable):
            raise VivadoNotFoundError(self._executable + " not found in PATH. Have you sourced Vivado\'s setup script?")

        # Define the prompt to use
        if prompt is None:
            # set prompt pattern based on sim variant
            self._prompt = self.__promptMap[executable]
        else:
            self._prompt = prompt

        # Set up the output formatter
        self._out = VivadoOutputFormatter(
            echoprefix if ( echoprefix or (sessionid is None) )
            else (sessionid + ' | '),
            quiet=(not echo)
        )

        self._out.write('\n' + '- Starting Vivado -'+'-' * 40 + '\n')
        self._out.quiet = (not echobanner)
       
        lLogName = self._executable + (('_' + sessionid) if sessionid else '')
        self._process = pexpect.spawn(self._executable,[
                    '-mode', 'tcl', 
                    '-log', lLogName+'.log',
                    '-journal', lLogName+'.jou'
                ],
            echo=echo,
            logfile=self._out,
            # preexec_fn=on_parent_exit('SIGTERM')
        )

        # Compile the list of patterns to detect the prompt
        self._rePrompt = self._process.compile_pattern_list(
            self.__newlines+[self._prompt, pexpect.TIMEOUT]
        )
        # Set send delay
        self._process.delaybeforesend = 0.00  # 1

        # Wait for vivado to wake up
        startupstr = self.__expectPrompt()
        
        # Extract version infomation
        self._variant, self._version = _parseversion(''.join(startupstr[0]))
        self._out.quiet = (not echo)
        self._log.debug('Vivado up and running')
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
    @property
    def echoprefix(self):
        return self._out.prefix

    # --------------------------------------------------------------
    @echoprefix.setter
    def echoprefix(self, prefix):
        self._out.prefix = prefix

    # --------------------------------------------------------------
    def __del__(self):
        self.close()

    # --------------------------------------------------------------
    def __call__(self, aCmd='', aMaxLen=1):
        # return self.execute(aCmd, aMaxLen)
        return self.execute(aCmd, aMaxLen)

    # --------------------------------------------------------------
    def __checkEcho(self, aText, aBefore):
        """
        Hard check: First line of output must match the injected command
        """

        lCmdRcvd = self.__reCharBackspace.sub('', aBefore)
        lCmdSent = aText.split('\n')[0]
        if lCmdRcvd != lCmdSent:
            # --------------------------------------------------------------
            print('-' * 20)
            print('Echo character-by-character diff')
            # Find where the 2 strings don't match
            print('sent:', len(lCmdSent), 'rcvd', len(lCmdRcvd))

            # find the first mismatching character
            minlen = min(len(lCmdRcvd), len(lCmdSent))
            maxlen = max(len(lCmdRcvd), len(lCmdSent))
            x = next((i for i in range(minlen) if lCmdRcvd[i] != lCmdSent[i]), minlen)

            a = x - 10
            b = x + 10
            for i in range(max(a, 0), min(b, maxlen)):
                r = lCmdRcvd[i] if len(lCmdRcvd) > i else ' '
                s = lCmdSent[i] if len(lCmdSent) > i else ' '
                # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s),
                # ord(s) > 128
                print(i, '\t', repr(s), repr(r), r == s, ord(r))

            print(''.join([str(i % 10) for i in range(len(lCmdRcvd))]))
            print(lCmdRcvd)
            print(''.join([str(i % 10) for i in range(len(lCmdSent))]))
            print(lCmdSent)
            # --------------------------------------------------------------
            raise RuntimeError(
                "Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(
                    lCmdSent, lCmdRcvd
                )
            )

    # --------------------------------------------------------------
    def __send(self, aText):

        x = self._process.sendline(aText)
        lIndex = self._process.expect(self.__newlines)

        # --------------------------------------------------------------
        # Hard check: First line of output must match the injected command
        self.__checkEcho(aText, self._process.before)


    # # --------------------------------------------------------------
    # def __send(self, aText, aChkEchoAck=True):
    #     self._process.sendline(aText)
    #     # --------------------------------------------------------------
    #     # Hard check: First line of output must match the injected command
    #     self._process.expect(self.__newlines)

    #     if not aChkEchoAck:
    #         return

    #     lCmdRcvd = self.__reCharBackspace.sub('', self._process.before)
    #     lCmdSent = aText.split('\n')[0]
    #     if lCmdRcvd != lCmdSent:
    #         # --------------------------------------------------------------
    #         print ('-' * 20)
    #         print ('Echo character-by-character diff')
    #         # Find where the 2 strings don't match
    #         print ('sent:', len(lCmdSent), 'rcvd', len(lCmdRcvd))
    #         for i in range(min(len(lCmdRcvd), len(lCmdSent))):
    #             r = lCmdRcvd[i]
    #             s = lCmdSent[i]
    #             # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s),
    #             # ord(s) > 128
    #             print (i, '\t', repr(r), repr(s), r == s, ord(r))

    #         print (''.join([str(i % 10) for i in range(len(lCmdRcvd))]))
    #         print (lCmdRcvd)
    #         print (''.join([str(i % 10) for i in range(len(lCmdSent))]))
    #         print (lCmdSent)
    #         # --------------------------------------------------------------
    #         raise RuntimeError(
    #             "Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(lCmdSent, lCmdRcvd))

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

            # ----------------------------------------------------------
            # Break if prompt
            if lIndex == 1:
                if not lBuffer:
                    lBuffer.append(None)
                break
            elif lIndex == 2:
                lTimeoutCounts += 1
                print ("VivadoConsole >> Time since last command: {0}s".format(
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

    # --------------------------------------------------------------
    def close(self):

        # Return immediately of already dead
        if not hasattr(self, '_process') or not self._process.isalive():
            self._log.debug('Vivado has already been stopped')
            # try:
            #   # I am being pedantic here, in case, for any reason, it wasn't done yet
            #   self.__instances.remove(self)
            # except KeyError:
            #   pass
            return

        self._log.debug('Shutting Vivado down')
        try:
            self.execute('quit')
        except pexpect.ExceptionPexpect:
            pass

        # Write one last newline
        self._out.write('- Terminating Vivado (pid {}) -'.format(self._process.pid)+'-' * 40 + '\n')
        # Just in case
        self._process.terminate(True)

        # Remove self from the list of instances
        self.__instances.remove(self)

    # # --------------------------------------------------------------
    # def execute(self, aCmd, aMaxLen=1):
    #     if not isinstance(aCmd, six.string_types):
    #         raise TypeError('expected string, found '+str(type(aCmd)))

    #     if aCmd.count('\n') != 0:
    #         raise ValueError('Format error. Newline not allowed in commands')

    #     self.__send(aCmd)
    #     lBuffer, lErrors, lCriticalWarnings = self.__expectPrompt(aMaxLen)

    #     if lErrors or (self._stopOnCWarnings and lCriticalWarnings):
    #         raise VivadoConsoleError(aCmd, lErrors, lCriticalWarnings)

    #     return list(lBuffer)

    # # --------------------------------------------------------------
    # def executeMany(self, aCmds, aMaxLen=1):
    #     if not isinstance(aCmds, list):
    #         raise TypeError('expected list')

    #     lOutput = []
    #     for lCmd in aCmds:
    #         lOutput.extend(self.execute(lCmd, aMaxLen))
    #     return lOutput
    
        # --------------------------------------------------------------
    def execute(self, aCmd, aMaxLen=1):
        if not isinstance(aCmd, six.string_types):
            raise TypeError('expected string, found '+str(type(aCmd)))

        if aCmd.count('\n') != 0:
            raise ValueError('Format error. Newline not allowed in commands')

        self.__send(aCmd)
        lBuffer, lErrors, lCriticalWarnings = self.__expectPrompt(aMaxLen)

        if lErrors or (self._stopOnCWarnings and lCriticalWarnings):
            raise VivadoConsoleError(aCmd, lErrors, lCriticalWarnings)

        return tuple(lBuffer)

    # # --------------------------------------------------------------
    # def executeMany(self, aCmds, aMaxLen=1):
    #     if not isinstance(aCmds, list):
    #         raise TypeError('expected list')

    #     lOutput = []
    #     for lCmd in aCmds:
    #         lOutput.extend(self.execute(lCmd, aMaxLen))
    #     return lOutput

    # --------------------------------------------------------------
    def changeMsgSeverity(self, aIds, aSeverity):
        """Change the severity of a single/multiple messages
        
        Args:
            aIds (str or list): List of message ids to update
            aSeverity (str): Target severity
        """
        lIds = aIds if isinstance(aIds, list) else [aIds]
        for c in ('set_msg_config -id {{{}}} -new_severity {{{}}}'.format(i, aSeverity) for i in lIds):
            self.execute(c)


#-------------------------------------------------------------------------------
@lazyctxmanager
class VivadoOpen(VivadoConsole):

    """Summary
    """
    
    pass

VivadoSnoozer = TCLConsoleSnoozer

@atexit.register
def __goodbye():
    VivadoConsole.killAllInstances()
# -------------------------------------------------------------------------
