from __future__ import print_function
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
from .common import which, OutputFormatter
from click import style
from .termui import *
from collections import Iterable

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
def autodetect(executable='vivado'):
    """
Vivado v2017.4 (64-bit)
SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
IP Build 2085800 on Fri Dec 15 22:25:07 MST 2017
Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.
    """

    lVerExpr = r'(Vivado[\s\w]*)\sv(\d+\.\d)'

    lVerRe = re.compile(lVerExpr, flags=re.IGNORECASE)

    if not which(executable):
        raise VivadoNotFoundError("%s not found in PATH. Have you sourced Vivado\'s setup script?" % executable)

    lExe = sh.Command(executable)
    lVerStr = lExe('-version')

    m = lVerRe.search(str(lVerStr))

    if m is None:
        raise VivadoNotFoundError("Failed to detect Vivado variant")

    return m.groups()
# ------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class VivadoBatch(object):
    """
    Wrapper class to run Vivado jobs in batch mode
    """
    _reInfo = re.compile(r'^INFO:')
    _reWarn = re.compile(r'^WARNING:')
    _reCritWarn = re.compile(r'^CRITICAL WARNING:')
    _reError = re.compile(r'^ERROR:')

    # --------------------------------------------
    def __init__(self, scriptpath=None, echo=False, log=None, cwd=None, dryrun=False):
        super(VivadoBatch, self).__init__()

        if scriptpath:
            _, lExt = splitext(scriptpath)
            if lExt not in ['.tcl', '.do']:
                raise ValueError('Unsupported extension {}. Use \'.tcl\' or \'.do\''.format(lExt))

        self.scriptpath = scriptpath
        self.log = log
        self.terminal = sys.stdout if echo else None
        self.cwd = cwd
        self.dryrun = dryrun
    # --------------------------------------------

    # --------------------------------------------
    def __enter__(self):
        self.script = (
            open(self.scriptpath, 'w') if self.scriptpath
            else tempfile.NamedTemporaryFile(suffix='.do')
        )
        return self
    # --------------------------------------------

    # --------------------------------------------
    def __exit__(self, type, value, traceback):
            if not self.dryrun:
                self._run()
            self.script.close()
    # --------------------------------------------

    # --------------------------------------------
    def __call__(self, *strings):
        for f in [self.script, self.terminal]:
            if not f:
                continue
            f.write(' '.join(strings) + '\n')
            f.flush()
    # --------------------------------------------

    # --------------------------------------------
    def _run(self):

        # Define custom log file
        lRoot, _ = splitext(basename(self.script.name))
        lLog = 'vivado_{0}.log'.format(lRoot)
        lJou = 'vivado_{0}.jou'.format(lRoot)

        # Guard against missing vivado executable
        if not which('vivado'):
            raise VivadoNotFoundError(
                '\'vivado\' not found in PATH. Have you sourced Vivado\'s setup script?'
            )

        sh.vivado('-mode', 'batch', '-source', self.script.name, '-log', lLog, '-journal', lJou, _out=sys.stdout, _err=sys.stderr)
        self.errors = []
        self.info = []
        self.warnings = []

        with open(lLog) as lLogFile:
            for i, l in enumerate(lLogFile):
                if self._reError.match(l):
                    self.errors.append((i, l))
                elif self._reWarn.match(l):
                    self.warnings.append((i, l))
                elif self._reInfo.match(l):
                    self.info.append((i, l))
    # --------------------------------------------
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
class VivadoOutputFormatter(OutputFormatter):
    """Formatter for Vivado command line output

    Arguments:
        prefix (string): String to prepend to each line of output
    """
    def __init__(self, prefix=None, quiet=False):
        super(VivadoOutputFormatter, self).__init__(prefix, quiet)

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
        isAlive (bool): Status of the vivado process
    
    """

    __reCharBackspace = re.compile(r'.\x08')
    __reError = re.compile(r'^ERROR:')
    __reCriticalWarning = re.compile(r'^CRITICAL WARNING:')
    __instances = set()
    __promptMap = {
        'vivado': r'Vivado%\s',
        'vivado_lab': r'vivado_lab%\s'
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
    def __init__(self, sessionid=None, echo=True, echoprefix=None, executable='vivado', prompt=None, stopOnCWarnings=False):
        """
        Args:
            sessionid (str): Name of the Vivado session
            echo (bool):
            echoprefix (str):
            executable (str):
            prompt (str):
            stopOnCWarnings (str):
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

        self._out.write('\n' + '-' * 40 + '\n')
        self._process = pexpect.spawn('{0} -mode tcl -log {1}.log -journal {1}.jou'.format(
            self._executable,
            self._executable + ('_' + sessionid) if sessionid else ''),
            echo=echo,
            logfile=self._out
        )

        self._process.delaybeforesend = 0.00  # 1

        # Wait for vivado to wake up
        self.__expectPrompt()
        self._log.debug('Vivado up and running')

        self._processinfo = psutil.Process(self._process.pid)
        # Method mapping
        self.isAlive = self._process.isalive
        # Add self to the list of instances
        self.__instances.add(self)

    # --------------------------------------------------------------
    def __del__(self):
        self.quit()

    # --------------------------------------------------------------
    def __call__(self, aCmd='', aMaxLen=1):
        return self.execute(aCmd, aMaxLen)

    # --------------------------------------------------------------
    def __send(self, aText):
        self._process.sendline(aText)
        # --------------------------------------------------------------
        # Hard check: First line of output must match the injected command
        lIndex = self._process.expect([r'\r\n'])

        lCmdRcvd = self.__reCharBackspace.sub('', self._process.before)
        lCmdSent = aText.split('\n')[0]
        if lCmdRcvd != lCmdSent:
            # --------------------------------------------------------------
            print ('-' * 20)
            print ('Echo character-by-character diff')
            # Find where the 2 strings don't match
            print ('sent:', len(lCmdSent), 'rcvd', len(lCmdRcvd))
            for i in xrange(min(len(lCmdRcvd), len(lCmdSent))):
                r = lCmdRcvd[i]
                s = lCmdSent[i]
                # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s),
                # ord(s) > 128
                print (i, '\t', r, s, r == s, ord(r))

            print (''.join([str(i % 10) for i in xrange(len(lCmdRcvd))]))
            print (lCmdRcvd)
            print (''.join([str(i % 10) for i in xrange(len(lCmdSent))]))
            print (lCmdSent)
            # --------------------------------------------------------------
            raise RuntimeError(
                "Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(lCmdSent, lCmdRcvd))

    # --------------------------------------------------------------
    def __expectPrompt(self, aMaxLen=100):
        # lExpectList = ['\r\n','Vivado%\t', 'ERROR:']
        lCpl = self._process.compile_pattern_list(
            [r'\r\n', self._prompt, pexpect.TIMEOUT]
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
            # print '>',self._process.before

            # ----------------------------------------------------------
            # Break if prompt
            if lIndex == 1:
                if not lBuffer:
                    lBuffer.append(None)
                break
            elif lIndex == 2:
                lTimeoutCounts += 1
                print ("<Time elapsed since last command: {0}s>".format(
                    lTimeoutCounts * self._process.timeout))
            # ----------------------------------------------------------

            # Store the output in the circular buffer
            lBuffer.append(self._process.before)

            if self.__reError.match(self._process.before):
                lErrors.append(self._process.before)

            if self.__reCriticalWarning.match(self._process.before):
                lCriticalWarnings.append(self._process.before)

        # --------------------------------------------------------------

        return lBuffer, lErrors, lCriticalWarnings

    # --------------------------------------------------------------
    def quit(self):

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
        self._out.write('-' * 40 + '\n')
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
            raise TypeError('expected string')

        if aCmd.count('\n') != 0:
            raise ValueError('Format error. Newline not allowed in commands')

        self.__send(aCmd)
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
        lIds = aIds if isinstance(aIds, Iterable) else [aIds]
        self.executeMany(['set_msg_config -id "{}" -new_severity "{}"'.format(i, aSeverity) for i in lIds])


# -------------------------------------------------------------------------
class VivadoHWServer(VivadoConsole):

    """Vivado Harware server object

    Exposes a standard interface for programming devices.
    """
    
    # --------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(VivadoHWServer, self).__init__(*args, **kwargs)

    # --------------------------------------------------------------
    def openHw(self):
        return self.execute('open_hw')

    # --------------------------------------------------------------
    def connect(self, uri=None):
        lCmd = ['connect_hw_server']
        if uri is not None:
            lCmd += ['-url ' + uri]
        return self.execute(' '.join(lCmd))

    # --------------------------------------------------------------
    def getHwTargets(self):
        return self.execute('get_hw_targets')[0].split()

    # --------------------------------------------------------------
    def openHwTarget(self, target):
        return self.execute('open_hw_target {{{0}}}'.format(target))

    # --------------------------------------------------------------
    def closeHwTarget(self, target=None):
        lCmd = 'close_hw_target' + ('' if target is None else ' ' + target)
        return self.execute(lCmd)

    # --------------------------------------------------------------
    def getHwDevices(self):
        return self.execute('get_hw_devices')[0].split()

    # --------------------------------------------------------------
    def programDevice(self, device, bitfile):
        from os.path import abspath, normpath

        bitpath = abspath(normpath(bitfile))

        self._log.debug('Programming %s with %s', device, bitfile)

        self.execute('current_hw_device {0}'.format(device))
        self.execute(
            'refresh_hw_device -update_hw_probes false [current_hw_device]'
        )
        self.execute('set_property PROBES.FILE {{}} [current_hw_device]')
        self.execute(
            'set_property PROGRAM.FILE {{{0}}} [current_hw_device]'.format(bitpath)
        )
        self.execute('program_hw_devices [current_hw_device]')


# -------------------------------------------------------------------------
class VivadoOpen(object):
    """VivadoConsole wrapper for with statements"""

    # --------------------------------------------------------------
    @property
    def quiet(self):
        return self._console.quiet

    # --------------------------------------------------------------
    @quiet.setter
    def quiet(self, value):
        self._console.quiet = value

    # --------------------------------------------------------------
    @property
    def console(self):
        return self._console

    # --------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(VivadoOpen, self).__init__()
        self._args = args
        self._kwargs = kwargs

    # --------------------------------------------------------------
    def __enter__(self):
        self._console = VivadoConsole(*self._args, **self._kwargs)
        return self

    # --------------------------------------------------------------
    def __exit__(self, type, value, traceback):
        self._console.quit()

    # --------------------------------------------------------------
    def __call__(self, aCmd=None, aMaxLen=1):
        # FIXME: only needed because of VivadoProjectMaker
        # Fix at source and remove
        if aCmd is None:
            return

        if aCmd.count('\n') is not 0:
            aCmd = aCmd.split('\n')

        if isinstance(aCmd, str):
            return self._console.execute(aCmd, aMaxLen)
        elif isinstance(aCmd, list):
            return self._console.executeMany(aCmd, aMaxLen)
        else:
            raise TypeError('Unsupported command type ' + type(aCmd).__name__)


# -------------------------------------------------------------------------
class VivadoSnoozer(object):
    """Snoozes notifications from Vivado """
    # --------------------------------------------------------------
    def __init__(self, aConsole):
        super(VivadoSnoozer, self).__init__()
        self._console = aConsole
        self._quiet = None
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __enter__(self):
        self._quiet = self._console.quiet
        self._console.quiet = True
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __exit__(self, type, value, traceback):
        self._console.quiet = self._quiet
    # --------------------------------------------------------------

# -------------------------------------------------------------------------


@atexit.register
def __goodbye():
    VivadoConsole.killAllInstances()
# -------------------------------------------------------------------------
