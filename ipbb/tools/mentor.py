from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import logging
import subprocess
import sys
import pexpect
import re
import collections
import os
import atexit
import sh

# Elements
from os.path import join, split, exists, splitext
from .common import which, OutputFormatter
from click import echo, secho, style

# Reminder, prompts are not all the same
# QuestaSim>
# ModelSim>
#

_vsim = 'vsim'
_vcom = 'vcom'


# --------------------------------------------------------------
def autodetect( executable = _vcom ):
    if not which(executable):
        raise ModelNotSimFoundError(
            "'%s' not found in PATH. Have you sourced Modelsim's setup script?" % executable)

    # lVsim = subprocess.Popen([executable, '-version'],
    #                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # lOut, lErr = lVsim.communicate()

    # if lVsim.returncode != 0:
    #     raise RuntimeError("Failed to execute %s" % executable)

    lVersion = sh.vsim('-version')

    if 'modelsim' in lVersion.lower():
        return 'ModelSim'
    elif 'questa' in lVersion.lower():
        return 'QuestaSim'
    else:
        raise RuntimeError("Failed to detect ModelSim/QuestaSim variant")
# --------------------------------------------------------------


# ------------------------------------------------
class ModelNotSimFoundError(Exception):

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(ModelNotSimFoundError, self).__init__(message)
# ------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ModelSimBatch(object):
    """docstring for VivadoBatch"""

    def __init__(self, script):
        super(ModelSimBatch, self).__init__()

        lBasename, lExt = splitext(script)
        if lExt != '.tcl':
            raise ValueError('Bugger off!!!')

        if not exists(script):
            raise ValueError("Script not found: '%s'" % script)

        # Guard against missing vivado executable
        if not which('vsim'):
            raise ModelNotSimFoundError(
                "'%s' not found in PATH. Have you sourced Modelsim's setup script?" % _vsim)

        self._script = script
        
        vsim = sh.Command(_vsim)
        vsim('-c', '-do', script, '-do', 'quit', _out=sys.stdout, _err=sys.stderr)

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ModelSimConsoleError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        command -- input command in which the error occurred
    """

    def __init__(self, errors, command):

        self.errors = errors
        self.command = command
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ModelSimConsole(object):
    """docstring for ModelSimConsole"""

    __reCharBackspace = re.compile(".\b")
    __reError = re.compile('^# \*\* Error')
    __instances = set()
    __promptMap = {
        'ModelSim': 'ModelSim> \rModelSim> ',
        'QuestaSim': 'QuestaSim> \rQuestaSim> '
    }
    __cmdPromptMaxLen = 500

    # --------------------------------------------------------------
    @classmethod
    def killAllInstances(cls):
        lInstances = set(cls.__instances)
        for lInstance in lInstances:
            lInstance.quit()
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __init__(self, sessionid=None, echo=True, echoprefix=None, executable=_vsim, prompt=None):
        super(ModelSimConsole, self).__init__()

        # Set up logger first
        self._log = logging.getLogger('Modelsim')
        self._log.debug('Starting Modelsim')

        # define what executable to run
        self._executable=executable
        if not which(self._executable):
            raise ModelsimNotFoundError(self._executable+" not found in PATH. Have you sourced Vivado\'s setup script?")

        # Define the prompt to use
        if prompt is None or prompt == 'autodetect':
            variant = autodetect(self._executable)
            # set prompt pattern based on sim variant
            self._prompt = self.__promptMap[variant]
        else:
            self._prompt = prompt

        # Modelsim doesn't like to operate without TERM (hangs)
        lEnv = dict(os.environ)
        if 'TERM' not in lEnv:
            lEnv['TERM'] = 'vt100'

        # Set up the output formatter
        self._out = OutputFormatter(
            echoprefix if ( echoprefix or (sessionid is None) ) 
                else (sessionid + ' | '),
            quiet = (not echo)
        )

        self._process = pexpect.spawn(
            '{0} -l {1}.log -c'.format(
                self._executable,
                'transcript' + ('_' + sessionid) if sessionid else ''
            ),
            env = lEnv,
            echo = echo,
            logfile = self._out
        )

        self._process.delaybeforesend = 0.00  # 1


        # Wait Modelsim to wake up
        self.__expectPrompt()
        self._log.debug('Modelsim up and running')

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

        x = self._process.sendline(aText)
        # --------------------------------------------------------------
        # Hard check: First line of output must match the injected command
        lIndex = self._process.expect(['\r\n', '\n\r'])

        lCmdRcvd = self.__reCharBackspace.sub('', self._process.before)
        lCmdSent = aText.split('\n')[0]
        if lCmdRcvd != lCmdSent:
            # --------------------------------------------------------------
            print ('-' * 20)
            # Find where the 2 strings don't match
            print (' sent:', len(lCmdSent), 'rcvd', len(lCmdRcvd))

            # find the first mismatching character
            minlen = min(len(lCmdRcvd), len(lCmdSent))
            maxlen = max(len(lCmdRcvd), len(lCmdSent))
            x = next( 
                (
                    i for i in xrange(minlen) 
                    if lCmdRcvd[i] != lCmdSent[i]
                ), minlen  
            )

            a = x-10
            b = x+10
            for i in xrange(max(a, 0),min(b, maxlen)):
                r = lCmdRcvd[i] if len(lCmdRcvd) > i else ' '
                s = lCmdSent[i] if len(lCmdSent) > i else ' '
                # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s),
                # ord(s) > 128
                print (i, '\t', repr(s),  repr(r), r == s, ord(r))

            print (''.join([str(i % 10) for i in xrange(len(lCmdRcvd))]))
            print (lCmdRcvd)
            print (''.join([str(i % 10) for i in xrange(len(lCmdSent))]))
            print (lCmdSent)
            # --------------------------------------------------------------
            raise RuntimeError(
                "Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(lCmdSent, lCmdRcvd))
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __expectPrompt(self, aMaxLen=100):
        # lExpectList = ['\r\n','Vivado%\t', 'ERROR:']
        lCpl = self._process.compile_pattern_list(
            ['\r\n', '\n\r', self._prompt, pexpect.TIMEOUT])
        lIndex = None
        lBuffer = collections.deque([], aMaxLen)
        lErrors = []

        # --------------------------------------------------------------
        while True:
            # Search for newlines, prompt, end-of-file
            lIndex = self._process.expect_list(lCpl)

            # ----------------------------------------------------------
            # Break if prompt
            if lIndex in [1, 2]:
                break
            elif lIndex == 3:
                print ('-->> timeout caught')
            # ----------------------------------------------------------

            # Store the output in the circular buffer
            lBuffer.append(self._process.before)

            if self.__reError.match(self._process.before):
                lErrors.append(self._process.before)
            # secho("'"+self._process.before+"'", fg='cyan')
            # secho(str(lErrors), fg='red')
        # --------------------------------------------------------------

        return lBuffer, (lErrors if lErrors else None)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def quit(self):

        # Return immediately of already dead
        if not hasattr(self, '_process') or not self._process.isalive():
            # self._log.debug('ModelSim has already been stopped')
            # try:
            #   # I am being pedantic here, in case, for any reason, it wasn't done yet
            #   self.__instances.remove(self)
            # except KeyError:
            #   pass
            return

        try:
            self.execute('quit')
        except pexpect.ExceptionPexpect:
            pass

        # Just in case
        self._process.terminate(True)

        self.__instances.remove(self)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def execute(self, aCmd, aMaxLen=1):
        if not isinstance(aCmd, str):
            raise TypeError('expected string')

        if aCmd.count('\n') != 0:
            raise ValueError('format error. Newline not allowed in commands')

        if len(aCmd) > self.__cmdPromptMaxLen:
            raise RuntimeError('modelsim prompt command length limited to 500 characters, while current command is {} characters long.'.format(len(aCmd)))

        self.__send(aCmd)
        lBuffer, lErrors = self.__expectPrompt(aMaxLen)
        if lErrors is not None:
            raise ModelSimConsoleError(lErrors, aCmd)
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
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ModelSimOpen(object):
    """docstring for ModelSimOpen"""

    # --------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(ModelSimOpen, self).__init__()
        self._args = args
        self._kwargs = kwargs
    # --------------------------------------------------------------
    
    # --------------------------------------------------------------
    def __enter__(self):
        self._console = ModelSimConsole(*self._args, **self._kwargs)
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
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@atexit.register
def __goodbye():
    ModelSimConsole.killAllInstances()
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
