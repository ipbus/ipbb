
import re
import os
import pexpect
import collections

import atexit
import logging

from ..utils import which, DEFAULT_ENCODING
from ..tcl_console import consolectxmanager, TCLConsoleSnoozer
from .sim_common import autodetect, ModelSimNotFoundError, ModelSimOutputFormatter, _vsim, _vcom

# ------------------------------------------------------------------
class ModelSimConsoleError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        command -- input command in which the error occurred
    """

    def __init__(self, errors, command):

        self.errors = errors
        self.command = command


# ------------------------------------------------------------------
class ModelSimConsole(object):
    """docstring for ModelSimConsole"""

    __reCharBackspace = re.compile(r'.\x08')
    __reError = re.compile(r'^# \*\* Error')
    __instances = set()
    __promptMap = {
        'ModelSim': r'ModelSim> \rModelSim> ',
        'QuestaSim': r'QuestaSim> \rQuestaSim> ',
    }
    __cmdPromptMaxLen = 500
    __newlines = ['\r\n', '\n\r']

    # --------------------------------------------------------------
    @classmethod
    def killAllInstances(cls):
        lInstances = set(cls.__instances)
        for lInstance in lInstances:
            lInstance.close()

    # --------------------------------------------------------------
    def __init__(self, executable=_vsim, prompt=None,  echo=True, sid=None, loglabel=None):
        super().__init__()

        # Set up logger first
        self._log = logging.getLogger('Modelsim')
        self._log.debug('Starting Modelsim')

        # define what executable to run
        self._executable = executable
        if not which(self._executable):
            raise ModelSimNotFoundError(
                self._executable
                + " not found in PATH. Have you sourced Vivado\'s setup script?"
            )

        # import pdb; pdb.set_trace()

        self._variant, self._version = autodetect()
        # Define the prompt to use
        if prompt is None or prompt == 'autodetect':
            # set prompt pattern based on sim variant
            self._prompt = self.__promptMap[self._variant]
        else:
            self._prompt = prompt

        

        # Modelsim doesn't like to operate without TERM (hangs)
        lEnv = dict(os.environ)
        if 'TERM' not in lEnv:
            lEnv['TERM'] = 'vt100'

        # Set up the output formatter
        self._out = ModelSimOutputFormatter(
            sid,
            quiet=(not echo),
        )
        # If loglabel is not specified, use sid
        loglabel = loglabel if loglabel else sid
        lLogName = 'transcript' + (('_' + loglabel) if loglabel else '')

        self._process = pexpect.spawn(self._executable, [
                    '-c', 
                    '-l', lLogName
                ],
            env=lEnv,
            echo=echo,
            logfile=self._out,
            encoding=DEFAULT_ENCODING,
        )

        self._process.delaybeforesend = 0.00  # 1

        # Compile the list of patterns to detect the prompt
        self._rePrompt = self._process.compile_pattern_list(
            self.__newlines+[self._prompt, pexpect.TIMEOUT]
        )

        # Wait Modelsim to wake up
        self.__expectPrompt()
        self._log.debug('Modelsim up and running')

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

        # --------------------------------------------------------------
        lTimeoutCounts = 0
        while True:
            # Search for newlines, prompt, end-of-file
            lIndex = self._process.expect_list(self._rePrompt)

            # ----------------------------------------------------------
            # Break if prompt
            if lIndex in [1, 2]:
                break
            elif lIndex == 3:
                lTimeoutCounts += 1
                print ("ModelsimConsole >> Time since last command: {0}s".format(
                    lTimeoutCounts * self._process.timeout))
            # ----------------------------------------------------------

            # Store the output in the circular buffer
            lBuffer.append(self._process.before)

            if self.__reError.match(self._process.before):
                lErrors.append(self._process.before)
        # --------------------------------------------------------------

        return lBuffer, (lErrors if lErrors else None)

    # --------------------------------------------------------------
    def close(self):

        # Return immediately of already dead
        if not hasattr(self, '_process') or not self._process.isalive():
            # self._log.debug('ModelSim has already been stopped')
            # try:
            #   # I am being pedantic here, in case, for any reason, it wasn't done yet
            #   self.__instances.remove(self)
            # except KeyError:
            #   pass
            return

        self._log.debug('Shutting Modelsim down')
        try:
            self.execute('quit')
        except pexpect.ExceptionPexpect:
            pass

        # Write one last newline
        self._out.write('- Terminating Modelsim (pid {}) -'.format(self._process.pid)+'-' * 40 + '\n')
        # Just in case
        self._process.terminate(True)

        self.__instances.remove(self)

    # --------------------------------------------------------------
    def execute(self, aCmd, aMaxLen=1):
        if not isinstance(aCmd, str):
            raise TypeError('expected string')

        if aCmd.count('\n') != 0:
            raise ValueError('format error. Newline not allowed in commands')

        if len(aCmd) > self.__cmdPromptMaxLen:
            raise RuntimeError(
                'modelsim prompt command length limited to 500 characters, while current command is {} characters long.'.format(
                    len(aCmd)
                )
            )

        self.__send(aCmd)
        lBuffer, lErrors = self.__expectPrompt(aMaxLen)
        if lErrors is not None:
            raise ModelSimConsoleError(lErrors, aCmd)

        return tuple(lBuffer)


#-------------------------------------------------------------------------------
@consolectxmanager
class ModelSimSession(ModelSimConsole):

    """Summary
    """
    
    pass


#-------------------------------------------------------------------------------
ModelSimSnoozer = TCLConsoleSnoozer



# ------------------------------------------------------------------
@atexit.register
def __goodbye():
    ModelSimConsole.killAllInstances()

