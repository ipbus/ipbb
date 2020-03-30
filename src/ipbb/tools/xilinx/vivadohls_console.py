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
from ..common import which, OutputFormatter
from ..termui import *

# ------------------------------------------------
class VivadoHLSNotFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(VivadoHLSNotFoundError, self).__init__(message)
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
    def __init__(self, prefix=None, quiet=False):
        super(VivadoHLSOutputFormatter, self).__init__(prefix, quiet)

        self.pendingchars = ''

    def write(self, message):
        """Writes formatted message
        
        Args:
            message (string): Message to format
        """
        # put any pending character first
        msg = self.pendingchars + message

        lines = msg.splitlines()

        if not message.endswith('\n'):
            self.pendingchars = lines[-1]
            del lines[-1]
        else:
            self.pendingchars = ''

        for lLine in lines:
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

            self._write((self.prefix if self.prefix else '') + lLine + '\n')
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

    __reCharBackspace = re.compile(u'.\x08')
    __reError = re.compile(u'^ERROR:')
    __reCriticalWarning = re.compile(u'^CRITICAL WARNING:')
    __instances = set()
    __promptMap = {
        'vivado_hls': u'vivado_hls>\s',
    }

    # --------------------------------------------------------------
    @classmethod
    def killAllInstances(cls):
        lInstances = set(cls.__instances)
        for lInstance in lInstances:
            lInstance.quit()
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
    def __init__(self, sessionid=None, echo=True, echobanner=False, echoprefix=None, executable='vivado_hls', prompt=None, stopOnCWarnings=False):
        """
        Args:
            sessionid (str): Name of the VivadoHLS session
            echo (bool): Switch to enable echo messages
            echoprefix (str): Prefix to echo message
            executable (str): Executable name
            prompt (str):
            stopOnCWarnings (bool): Stop on Critical Warnings
        """
        super(VivadoHLSConsole, self).__init__()

        # Set up logger first
        self._log = logging.getLogger('VivadoHLS')
        self._log.debug('Starting VivadoHLS')

        self._stopOnCWarnings = stopOnCWarnings
        # define what executable to run
        self._executable = executable
        if not which(self._executable):
            raise VivadoNotFoundError(self._executable + " not found in PATH. Have you sourced VivadoHLS\'s setup script?")

        # Define the prompt to use
        if prompt is None:
            # set prompt pattern based on sim variant
            self._prompt = self.__promptMap[executable]
        else:
            self._prompt = prompt

        # Set up the output formatter
        self._out = VivadoHLSOutputFormatter(
            echoprefix if ( echoprefix or (sessionid is None) )
            else (sessionid + ' | '),
            quiet=(not echo)
        )

        self._out.write('\n' + '- Starting VivadoHLS -'+'-' * 40 + '\n')
        self._out.quiet = (not echobanner)
       
        # self._process = pexpect.spawnu('{0} -mode tcl -log {1}.log -journal {1}.jou'.format(
        self._process = pexpect.spawn('{0} -i -l {1}.log'.format(
            self._executable,
            self._executable + ('_' + sessionid) if sessionid else ''),
            echo=echo,
            logfile=self._out,
            # preexec_fn=on_parent_exit('SIGTERM')
        )

        self._process.delaybeforesend = 0.00  # 1

        # Wait for vivadoHLS to wake up
        startupstr = self.__expectPrompt()
        self._variant, self._version = _parseversion(''.join(startupstr[0]))
        self._out.quiet = (not echo)
        self._log.debug('VivadoHLS up and running')
        self._out.write('\n' + '- Started {} {} -'.format(self.variant, self.version)+'-' * 40 + '\n')

        self._processinfo = psutil.Process(self._process.pid)
        # Method mapping
        self.isAlive = self._process.isalive
        # Add self to the list of instances
        self.__instances.add(self)

    @property
    def variant(self):
        return self._variant
    
    @property
    def version(self):
        return self._version
    

    # --------------------------------------------------------------
    def __del__(self):
        self.quit()

    # --------------------------------------------------------------
    def __call__(self, aCmd='', aMaxLen=1):
        return self.execute(aCmd, aMaxLen)

    # --------------------------------------------------------------
    def __send(self, aText, e=True):
        self._process.sendline(aText)
        if not aChkEchoAck:
            return
        # --------------------------------------------------------------
        # Hard echo check: First line of output must match the injected command
        self._process.expect([u'\r\n'])

        lCmdRcvd = self.__reCharBackspace.sub('', self._process.before)
        lCmdSent = aText.split('\n')[0]

        if lCmdRcvd != lCmdSent:
            # --------------------------------------------------------------
            print ('-' * 20)
            print ('Echo character-by-character diff')
            # Find where the 2 strings don't match
            print ('sent:', len(lCmdSent), 'rcvd', len(lCmdRcvd))
            for i in range(min(len(lCmdRcvd), len(lCmdSent))):
                r = lCmdRcvd[i]
                s = lCmdSent[i]
                # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s),
                # ord(s) > 128
                print (i, '\t', r, s, r == s, ord(r))

            print (''.join([str(i % 10) for i in range(len(lCmdRcvd))]))
            print (lCmdRcvd)
            print (''.join([str(i % 10) for i in range(len(lCmdSent))]))
            print (lCmdSent)
            # --------------------------------------------------------------
            raise RuntimeError(
                "Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(lCmdSent, lCmdRcvd))

    # --------------------------------------------------------------
    def __expectPrompt(self, aMaxLen=100):
        lCpl = self._process.compile_pattern_list(
            [u'\r\n', self._prompt, pexpect.TIMEOUT]
        )
        lIndex = None
        lBuffer = collections.deque([], aMaxLen)
        lErrors = []
        lCriticalWarnings = []

        # --------------------------------------------------------------
        lTimeoutCounts = 0
        while True:
            # Search for newlines, prompt, end-of-file
            lIndex = self._process.expect_list(lCpl)
            print("zzzz",lIndex, repr(self._process.before))

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
    def quit(self):

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
            self.__send('quit', False)
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
        if not isinstance(aCmd, six.string_types):
            raise TypeError('expected string, found '+str(type(aCmd)))

        if aCmd.count('\n') != 0:
            raise ValueError('Format error. Newline not allowed in commands')

        self.__send(aCmd, False)
        lBuffer, lErrors, lCriticalWarnings = self.__expectPrompt(aMaxLen)

        if lErrors or (self._stopOnCWarnings and lCriticalWarnings):
            raise VivadoConsoleError(aCmd, lErrors, lCriticalWarnings)

        return list(lBuffer)

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


@atexit.register
def __goodbye():
    VivadoHLSConsole.killAllInstances()
# -------------------------------------------------------------------------