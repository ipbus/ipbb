from __future__ import print_function
#------------------------------------------------------------------------------

# Modules
import subprocess
import pexpect
import sys
import re
import collections
import os
import atexit

# Elements
from os.path import join, split, exists, splitext
from .common import which

# Prompts
# QuestaSim>
# ModelSim>
# 

_vsim = 'vsim'

#--------------------------------------------------------------
def autodetect():
  if not which(_vsim):
    raise ModelNotSimFoundError("'%s' not found in PATH. Have you sourced Modelsim's setup script?" % _vsim)

  lVsim = subprocess.Popen(['vsim','-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  lOut, lErr = lVsim.communicate()

  if lVsim.returncode != 0:
    raise RuntimeError("Failed to execute %s" % _vsim)

  if 'modelsim' in lOut.lower():
    return 'ModelSim'
  elif 'questa' in lOut.lower():
    return 'QuestaSim'
  else:
    raise RuntimeError("Failed to detect ModelSim/QuestaSim variant")
#--------------------------------------------------------------

#------------------------------------------------
class ModelNotSimFoundError(Exception):

  def __init__(self, message):
    # Call the base class constructor with the parameters it needs
    super(ModelNotSimFoundError, self).__init__(message)
#------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
      raise ModelNotSimFoundError("'%s' not found in PATH. Have you sourced Modelsim's setup script?" % _vsim)

    self._script = script

    cmd = [_vsim, '-c', '-do', 'do %s; quit' % script]
    process = subprocess.Popen(cmd)

    process.wait()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ModelSimConsole(object):
  """docstring for ModelSimConsole"""

  __reCharBackspace = re.compile(".\b")
  __instances = set()

  #--------------------------------------------------------------
  @classmethod
  def killAllInstances(cls):
    lInstances = set(cls.__instances)
    for lInstance in lInstances:
      lInstance.quit()
  #--------------------------------------------------------------

  def __init__(self):
    super(ModelSimConsole, self).__init__()

    # Guard against missing vivado executable 
    # if not which(_vsim):
      # raise ModelNotSimFoundError('\'%s\' not found in PATH. Have you sourced Modelsim\'s setup script?' % _vsim)

    self.variant = autodetect()
    # set prompt pattern based on sim variant
    self._prompt = {
      'ModelSim':'ModelSim> ',
      'QuestaSim':'QuestaSim> '
      }[self.variant]

    self._process = pexpect.spawn('%s -c' % _vsim, maxread=1)
    self._process.logfile = sys.stdout
    self._process.delaybeforesend = 0.00 #1
    self.__expectPrompt()
    self.isAlive = self._process.isalive
    self.__instances.add(self)

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
      return

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
    lIndex = self._process.expect(['\r\n'])
    
    lCmdRcvd = self.__reCharBackspace.sub('',self._process.before)
    lCmdSent = aText.split('\n')[0]
    if lCmdRcvd != lCmdSent:
      #--------------------------------------------------------------
      # Find where the 2 strings don't match
      print (len(lCmdRcvd), len(lCmdSent))
      for i in xrange(min(len(lCmdRcvd), len(lCmdSent))):
          r = lCmdRcvd[i]
          s = lCmdSent[i]
          # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s), ord(s) > 128 
          print (i, '\t', r, s, r==s, ord(r))

      print (''.join([str(i%10) for i in xrange(len(lCmdRcvd))]))
      print (lCmdRcvd)
      print (''.join([str(i%10) for i in xrange(len(lCmdSent))]))
      print (lCmdSent)
      #--------------------------------------------------------------
      raise RuntimeError("Command and first output lines don't match Sent='{0}', Rcvd='{1}".format(lCmdSent,lCmdRcvd))
    #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __expectPrompt(self, aMaxLen=100):
    # lExpectList = ['\r\n','Vivado%\t', 'ERROR:']
    lCpl = self._process.compile_pattern_list(['\r\n',self._prompt,pexpect.TIMEOUT])
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
        print ('-->> timeout caught')
      #----------------------------------------------------------

      # Store the output in the circular buffer
      lBuffer.append(self._process.before)

      # Fixme
      # if self.__reError.match(self._process.before):
        # lErrors.append(self._process.before)
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
      raise VivadoConsoleError(lErrors, aCmd)
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

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@atexit.register
def __goodbye():
    ModelSimConsole.killAllInstances()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

