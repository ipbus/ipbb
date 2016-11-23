import logging
import pexpect
import sys
import re
import collections
import subprocess
import os.path
import atexit

#------------------------------------------------
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
#------------------------------------------------


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Batch(object):
  """docstring for Batch"""

  reInfo = re.compile('^INFO:')
  reWarn = re.compile('^WARNING:')
  reError = re.compile('^ERROR:')

  def __init__(self, script):
    super(Batch, self).__init__()

    lBasename, lExt = os.path.splitext(script)

    if lExt != '.tcl':
      raise RuntimeError('Bugger off!!!')

    self._script = script
    self._log = 'vivado_{0}.log'.format(lBasename)

    cmd = 'vivado -mode batch -source {0} -log {1} -nojournal'.format(self._script, self._log)
    process = subprocess.Popen(cmd.split())
    process.wait()

    self.errors = []
    self.info = []
    self.warnings = []

    with  open(self._log) as lLog:
      for i,l in enumerate(lLog):
        if self.reError.match(l): self.errors.append( (i,l) )
        elif self.reWarn.match(l): self.warnings.append( (i,l) )
        elif self.reInfo.match(l): self.info.append( (i,l) )
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ConsoleError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        command -- input command in which the error occurred
    """

    def __init__(self, errors, command):
        self.errors = errors
        self.command = command
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class SmartConsole(object):
  """docstring for SmartConsole"""

  #--------------------------------------------------------------
  def __init__(self):
    super(SmartConsole, self).__init__()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __enter__(self):
    self._console = Console()
    return self
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __exit__(self, type, value, traceback):
    self._console.quit()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __call__(self, aCmd='', aMaxLen=1):
    return self._console(aCmd, aMaxLen)
  #--------------------------------------------------------------
    
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Console(object):
  """docstring for Vivado"""

  __reCharBackspace = re.compile(".\b")
  __reError = re.compile('^ERROR:')
  __instances = set()

  #--------------------------------------------------------------
  @classmethod
  def killAllInstances(cls):
    lInstances = set(cls.__instances)
    for lInstance in lInstances:
      lInstance.quit()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __init__(self):
    super(Console, self).__init__()
    self._log = logging.getLogger('Vivado')
    self._log.debug('Starting Vivado')
    self._process = pexpect.spawn('vivado -mode tcl',maxread=1)
    self._process.logfile = sys.stdout
    self._process.delaybeforesend = 0.00 #1
    self.__expectPrompt()
    self._log.debug('Vivado up and running')
    # Method mapping
    self.isAlive = self._process.isalive
    # Add self to the list of instances
    self.__instances.add(self)
    print self._process
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __del__(self):
    self.quit()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __call__(self, aCmd='', aMaxLen=1):
    return self.execute(aCmd, aMaxLen)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def quit(self):
    # Return immediately of already dead
    if not self._process.isalive():
      self._log.debug('Vivado has already been stopped')
      return

    self._log.debug('Shutting Vivado down')
    try:
      self.execute('quit')
    except pexpect.ExceptionPexpect as e:
      pass

    # Just in case
    self._process.terminate(True)

    self.__instances.remove(self)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __send(self, aText):

    self._process.sendline(aText)
    #--------------------------------------------------------------
    # Hard check: First line of output must match the injected command
    self._process.expect(['\r\n',pexpect.EOF])
    lCmdRcvd = self.__reCharBackspace.sub('',self._process.before)
    lCmdSent = aText.split('\n')[0]
    if lCmdRcvd != lCmdSent:
      #--------------------------------------------------------------
      # Find where the 2 strings don't match
      print len(lCmdRcvd), len(lCmdSent)
      for i in xrange(min(len(lCmdRcvd), len(lCmdSent))):
          r = lCmdRcvd[i]
          s = lCmdSent[i]
          # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s), ord(s) > 128 
          print i, '\t', r, s, r==s, ord(r)

      print ''.join([str(i%10) for i in xrange(len(lCmdRcvd))])
      print lCmdRcvd
      print ''.join([str(i%10) for i in xrange(len(lCmdSent))])
      print lCmdSent
      #--------------------------------------------------------------
      raise RuntimeError('Command and first output line don\'t match Sent=\'{0}\', Rcvd=\'{1}\''.format(lCmdSent,lCmdRcvd))
    #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __expectPrompt(self, aMaxLen=100):
    # lExpectList = ['\r\n','Vivado%\t', 'ERROR:']
    lCpl = self._process.compile_pattern_list(['\r\n','Vivado%\t',pexpect.TIMEOUT])
    lIndex = None
    lBuffer = collections.deque([],aMaxLen)
    lErrors = []

    #--------------------------------------------------------------
    while True:
      # Search for newlines, prompt, end-of-file
      # lIndex = self._process.expect(['\r\n','Vivado%\t', 'ERROR:', pexpect.EOF])
      lIndex = self._process.expect_list(lCpl)
      # print '>',self._process.before


      #----------------------------------------------------------
      # Break if prompt 
      if lIndex == 1:
        break
      elif lIndex == 2:
        print '-->> timeout caught'
      #----------------------------------------------------------

      # Store the output in the circular buffer
      lBuffer.append(self._process.before)

      if self.__reError.match(self._process.before):
        lErrors.append(self._process.before)
    #--------------------------------------------------------------

    return lBuffer,(lErrors if lErrors else None)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def execute(self, aCmd, aMaxLen=1):
    if not isinstance(aCmd,str):
      raise TypeError('expected string')

    if aCmd.count('\n') != 0:
      raise ValueError('format error. Newline not allowed in commands')

    self.__send(aCmd)
    lBuffer,lErrors = self.__expectPrompt(aMaxLen)
    if lErrors is not None:
      raise ConsoleError(lErrors, aCmd)
    return list(lBuffer)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def executeMany(self, aCmds, aMaxLen=1):
    if not isinstance(aCmds,list):
      raise TypeError('expected list')

    lOutput = []
    for lCmd in aCmds:
      lOutput.extend(self.execute(lCmd, aMaxLen))
    return lOutput
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def openHw(self):
    return self.execute('open_hw')
  #--------------------------------------------------------------
      
  #--------------------------------------------------------------
  def connect(self,uri):
    return self.execute('connect_hw_server -url %s' % uri)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getHwTargets(self):
    return self.execute('get_hw_targets')[0].split()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def openHwTarget(self, target):
    return self.execute('open_hw_target {{{0}}}'.format(target))
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getHwDevices(self):
      return self.execute('get_hw_devices')[0].split()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def programDevice(self, device, bitfile):
      from os.path import abspath, normpath

      bitpath = abspath(normpath(bitfile))

      self._log.debug('Programming %s with %s',device, bitfile)

      self.execute('current_hw_device {0}'.format(device))
      self.execute('refresh_hw_device -update_hw_probes false [current_hw_device]')
      self.execute('set_property PROBES.FILE {{}} [current_hw_device]')
      self.execute('set_property PROGRAM.FILE {{{0}}} [current_hw_device]'.format(bitpath))
      self.execute('program_hw_devices [current_hw_device]')
  #--------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@atexit.register
def __goodbye():
    Console.killAllInstances()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

