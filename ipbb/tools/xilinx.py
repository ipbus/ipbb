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

# Elements
from .common import which, OutputFormatter

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


# -------------------------------------------------------------------------
class VivadoBatch(object):
    """docstring for VivadoBatch"""

    _reInfo = re.compile('^INFO:')
    _reWarn = re.compile('^WARNING:')
    _reError = re.compile('^ERROR:')

    def __init__(self, script):
        super(VivadoBatch, self).__init__()

        lBasename, lExt = os.path.splitext(script)

        if lExt != '.tcl':
            raise RuntimeError('Bugger off!!!')

        self._script = script

        # Define custom log file
        self._log = 'vivado_{0}.log'.format(lBasename)

        # Guard against missing vivado executable
        if not which('vivado'):
            raise VivadoNotFoundError(
                '\'vivado\' not found in PATH. Have you sourced Vivado\'s setup script?')

        cmd = 'vivado -mode batch -source {0} -log {1} -nojournal'.format(
            self._script, self._log)
        process = subprocess.Popen(cmd.split())

        process.wait()

        self.errors = []
        self.info = []
        self.warnings = []

        with open(self._log) as lLog:
            for i, l in enumerate(lLog):
                if self._reError.match(l):
                    self.errors.append((i, l))
                elif self._reWarn.match(l):
                    self.warnings.append((i, l))
                elif self._reInfo.match(l):
                    self.info.append((i, l))
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
class VivadoConsoleError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        command -- input command in which the error occurred
    """

    def __init__(self, errors, command):

        self.errors = errors
        self.command = command
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
class VivadoConsole(object):
    """docstring for Vivado"""

    __reCharBackspace = re.compile(".\b")
    __reError = re.compile('^ERROR:')
    __instances = set()
    __promptMap = {
        'vivado': 'Vivado%[ \t]',
        'vivado_lab': 'vivado_lab%[ \t]'
    }
    # --------------------------------------------------------------
    @classmethod
    def killAllInstances(cls):
        lInstances = set(cls.__instances)
        for lInstance in lInstances:
            lInstance.quit()
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __init__(self, sessionid=None, echo=True, echoprefix=None, executable='vivado', prompt=None):
        super(VivadoConsole, self).__init__()

        # Set up logger first
        self._log = logging.getLogger('Vivado')
        self._log.debug('Starting Vivado')

        # define what executable to run
        self._executable=executable
        if not which(self._executable):
            raise VivadoNotFoundError(self._executable+" not found in PATH. Have you sourced Vivado\'s setup script?")

        # Define the prompt to use
        if prompt is None:
            # set prompt pattern based on sim variant
            self._prompt = self.__promptMap[executable]
        else:
            self._prompt = prompt

        # Set up the output formatter
        self._out = OutputFormatter(
            echoprefix if ( echoprefix or (sessionid is None) ) 
                else (sessionid + ' | '),
            quiet = (not echo)
        )

        self._process = pexpect.spawn('{0} -mode tcl -log {1}.log -journal {1}.jou'.format(
            self._executable,
            self._executable + ('_' + sessionid) if sessionid else ''),
            echo = echo,
            logfile = self._out
        )

        self._process.delaybeforesend = 0.00  # 1

        # Wait for vivado to wake up
        self.__expectPrompt()
        self._log.debug('Vivado up and running')

        # Method mapping
        self.isAlive = self._process.isalive
        # Add self to the list of instances
        self.__instances.add(self)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __del__(self):
        self.quit()
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __call__(self, aCmd='', aMaxLen=1):
        return self.execute(aCmd, aMaxLen)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __send(self, aText):

        self._process.sendline(aText)
        # --------------------------------------------------------------
        # Hard check: First line of output must match the injected command
        lIndex = self._process.expect(['\r\n'])

        lCmdRcvd = self.__reCharBackspace.sub('', self._process.before)
        lCmdSent = aText.split('\n')[0]
        if lCmdRcvd != lCmdSent:
            # --------------------------------------------------------------
            print ('-' * 20)
            # Find where the 2 strings don't match
            print (' sent:', len(lCmdSent), 'rcvd', len(lCmdRcvd))
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
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __expectPrompt(self, aMaxLen=100):
        # lExpectList = ['\r\n','Vivado%\t', 'ERROR:']
        lCpl = self._process.compile_pattern_list(
            ['\r\n', self._prompt, pexpect.TIMEOUT])
        lIndex = None
        lBuffer = collections.deque([], aMaxLen)
        lErrors = []

        # --------------------------------------------------------------
        lTimeoutCounts = 0
        while True:
            # Search for newlines, prompt, end-of-file
            lIndex = self._process.expect_list(lCpl)
            # print '>',self._process.before

            # ----------------------------------------------------------
            # Break if prompt
            if lIndex == 1:
                break
            elif lIndex == 2:
                lTimeoutCounts += 1
                print ("<Time elapsed: {0}s>".format(
                    lTimeoutCounts * self._process.timeout))
            # ----------------------------------------------------------

            # Store the output in the circular buffer
            lBuffer.append(self._process.before)

            if self.__reError.match(self._process.before):
                lErrors.append(self._process.before)
        # --------------------------------------------------------------

        return lBuffer, (lErrors if lErrors else None)
    # --------------------------------------------------------------

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
        except pexpect.ExceptionPexpect as e:
            pass

        # Just in case
        self._process.terminate(True)

        # Remove self from the list of instances
        self.__instances.remove(self)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    @property
    def echoprefix(self):
        return self._out.prefix
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    @echoprefix.setter
    def echoprefix(self, prefix):
        self._out.prefix = prefix
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def execute(self, aCmd, aMaxLen=1):
        if not isinstance(aCmd, str):
            raise TypeError('expected string')

        if aCmd.count('\n') != 0:
            raise ValueError('format error. Newline not allowed in commands')

        self.__send(aCmd)
        lBuffer, lErrors = self.__expectPrompt(aMaxLen)
        if lErrors is not None:
            raise VivadoConsoleError(lErrors, aCmd)
        return list(lBuffer)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def executeMany(self, aCmds, aMaxLen=1):
        if not isinstance(aCmds, list):
            raise TypeError('expected list')

        lOutput = []
        for lCmd in aCmds:
            lOutput.extend(self.execute(lCmd, aMaxLen))
        return lOutput
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def openHw(self):
        return self.execute('open_hw')
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def connect(self, uri=None):
        lCmd = ['connect_hw_server']
        if uri is not None:
            lCmd += ['-url '+uri]
        return self.execute(' '.join(lCmd))
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def getHwTargets(self):
        return self.execute('get_hw_targets')[0].split()
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def openHwTarget(self, target):
        return self.execute('open_hw_target {{{0}}}'.format(target))
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def closeHwTarget(self, target=None):
        lCmd = 'close_hw_target' + ('' if target is None else ' ' + target)
        return self.execute(lCmd)
    # --------------------------------------------------------------
    
    # --------------------------------------------------------------
    def getHwDevices(self):
        return self.execute('get_hw_devices')[0].split()
    # --------------------------------------------------------------

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
    # --------------------------------------------------------------
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
class VivadoOpen(object):
    """docstring for VivadoOpen"""

    # --------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(VivadoOpen, self).__init__()
        self._args = args
        self._kwargs = kwargs
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __enter__(self):
        self._console = VivadoConsole(*self._args, **self._kwargs)
        return self
    # --------------------------------------------------------------
    
    # --------------------------------------------------------------
    def __exit__(self, type, value, traceback):
        self._console.quit()
    # --------------------------------------------------------------

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
    # --------------------------------------------------------------
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------


@atexit.register
def __goodbye():
    VivadoConsole.killAllInstances()
# -------------------------------------------------------------------------
