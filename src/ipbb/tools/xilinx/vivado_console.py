
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
from ...utils import which, DEFAULT_ENCODING
# from ..termui import *
from ..tcl_console import consolectxmanager, TCLConsoleSnoozer
from .vivado_common import VivadoNotFoundError, autodetect, VivadoOutputFormatter, _parseversion

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
class VivadoConsole(object):
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
        'vivado': re.compile(r'Vivado%\s'),
        'vivado_lab': re.compile(r'vivado_lab%\s')
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
    def __init__(self, executable='vivado', prompt=None, stopOnCWarnings=False, echo=True, showbanner=False, sid=None, loglabel=None, loglevel='all'):
        """
        Args:
            executable (str): Executable name
            prompt (std, optional): Prompt string
            stopOnCWarnings (bool): Stop on Critical Warnings
            echo (bool): Switch to enable echo messages
            showbanner (bool, optional): Show Vivado startup banner
            sid (str): Session id
            loglabel (None, optional): log files name
        
        Raises:
            VivadoNotFoundError: Description
        
        """
        super().__init__()

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
            sid, loglevel=loglevel
        )

        self._out.write('\n' + '- Starting Vivado -'+'-' * 40 + '\n')
        self._out.quiet = (not showbanner)
       
        # If loglabel is not specified, use sid
        loglabel = loglabel if loglabel else sid
        lLogName = self._executable + (('_' + loglabel) if loglabel else '')
        self._process = pexpect.spawn(self._executable,[
                    '-mode', 'tcl', 
                    '-log', lLogName+'.log',
                    '-journal', lLogName+'.jou'
                ],
            echo=echo,
            logfile=self._out,
            encoding=DEFAULT_ENCODING,
            preexec_fn=on_parent_exit('SIGTERM')
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
    def stopOnCWarnings(self):
        return self._stopOnCWarnings
    
    # --------------------------------------------------------------
    @stopOnCWarnings.setter
    def stopOnCWarnings(self, stop):
        self._stopOnCWarnings = stop

    # --------------------------------------------------------------
    @property
    def sessionid(self):
        return self._out.prefix

    # --------------------------------------------------------------
    @sessionid.setter
    def sessionid(self, prefix):
        self._out.prefix = prefix


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


    
    # --------------------------------------------------------------
    def execute(self, aCmd, aMaxLen=1):
        if not isinstance(aCmd, str):
            raise TypeError('expected string, found '+str(type(aCmd)))

        if aCmd.count('\n') != 0:
            raise ValueError('Format error. Newline not allowed in commands')

        self.__send(aCmd)
        lBuffer, lErrors, lCriticalWarnings = self.__expectPrompt(aMaxLen)

        if lErrors or (self._stopOnCWarnings and lCriticalWarnings):
            raise VivadoConsoleError(aCmd, lErrors, lCriticalWarnings)

        return tuple(lBuffer)

    # --------------------------------------------------------------
    def changeMsgSeverity(self, aIds, aSeverity):
        """Change the severity of a single/multiple messages
        
        Args:
            aIds (str or list): List of message ids to update
            aSeverity (str): Target severity
        """
        lIds = aIds if isinstance(aIds, list) else [aIds]
        for c in ('reset_msg_config -id {{{}}} -default_severity; set_msg_config -id {{{}}} -new_severity {{{}}}'.format(i, i, aSeverity) for i in lIds):
            self.execute(c)


#-------------------------------------------------------------------------------
@consolectxmanager
class VivadoSession(VivadoConsole):

    """Summary
    """
    pass


#-------------------------------------------------------------------------------
VivadoSnoozer = TCLConsoleSnoozer


# ------------------------------------------------------------------------------
class VivadoSessionContextAdapter(object):

    """Summary
    """

    def __init__(self, aManager, aCloseOnExit, aSId):
        """
        Constructor
        
        Args:
            aManager (VivadoSessionManager): Manager object
            aSId (str): SessionID
        
        """
        super().__init__()
        self._console = None
        self._mgr = aManager
        self._sid = aSId
        self._closeonexit = aCloseOnExit

    def __enter__(self):
        self._console = self._mgr._getconsole(sid=self._sid)
        return self._console

    def __exit__(self, type, value, traceback):
        if self._closeonexit:
            self._console.close()
            self._console = None
    

# ------------------------------------------------------------------------------
class VivadoSessionManager(object):
    """docstring for VivadoSessionManager
    
    Attributes:
        persistent (TYPE): Description
    """
    def __init__(self, keep=False, echo=True, loglabel=None, loglevel='all'):
        """Constructor
        
        Args:
            keep (TYPE): Description
        """
        super().__init__()
        self._keep = keep
        self._echo = echo
        self._loglabel = loglabel
        self._loglevel = loglevel
        if self._keep:
            self._console = None

    def __del__(self):
        if self._keep and self._console:
            self._console.close()

    def _getconsole(self, sid):

        if self._keep:
            if not self._console:
                self._console = VivadoConsole(sid=sid, loglabel=self._loglabel, echo=self._echo, loglevel=self._loglevel)
            self._console.sessionid = sid
            return self._console
        else:
            return VivadoConsole(sid=sid, loglabel=self._loglabel, echo=self._echo, loglevel=self._loglevel)


    def getctx(self, sid):
        """Session getter.
        
        Args:
            sid (str): Session identifier
        
        Returns:
            VivadoSessionContextAdapter: Context adapter holding the session details
        """
        return VivadoSessionContextAdapter(self, not self._keep, sid)


@atexit.register
def __goodbye():
    VivadoConsole.killAllInstances()
# -------------------------------------------------------------------------
