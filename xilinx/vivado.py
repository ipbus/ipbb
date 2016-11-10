import logging
import pexpect
import sys
import re
import collections


class Vivado(object):
  """docstring for Vivado"""

  __char_backspace = re.compile(".\b")
  
  #--------------------------------------------------------------
  def __init__(self):
    super(Vivado, self).__init__()
    self._log = logging.getLogger('Vivado')
    self._log.debug('Starting Vivado')
    self._me = pexpect.spawn('vivado -mode tcl')
    self._me.logfile = sys.stdout
    self.__expectprompt()
    self._log.debug('Vivado up and running')
  #--------------------------------------------------------------

        # print self._me.before

  #--------------------------------------------------------------
  def __del__(self):
    self.execute('quit')
    self._me.close()
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __send(self, aText):

    #--------------------------------------------------------------
    # Hard check: First line of output must match the injected command
    self._me.expect('\r\n')
    lCmdRcvd = self.__char_backspace.sub('',self._me.before)
    lCmdSent = aText
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

  def __expectPrompt(self, aMaxLen):
    lExpectList = ['\r\n','Vivado%\t', 'ERROR:']
    lIndex = None
    lBuffer = collections.deque([],aMaxLen)

    #--------------------------------------------------------------
    while True:
      # Search for newlines, prompt, end-of-file
      # lIndex = self._me.expect(['\r\n','Vivado%\t', 'ERROR:', pexpect.EOF])
      lIndex = self._me.expect(lExpectList)
      # print '>',self._me.before


      #----------------------------------------------------------
      # Break if prompt
      if lIndex == 1:
        break
      # or do something smart fi an error is caugth
      elif lIndex == 2:
        print 'ERROR detected'
      #----------------------------------------------------------

      # Store the output in the circular buffer
      lBuffer.append(self._me.before)
    #--------------------------------------------------------------

    return lBuffer
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def execute(self, aText):
    if isinstance(aText, str):
      lCmds = [aText]
    elif isinstance(aText, list):
      lCmds = aText

    lOutput = []
    for lCmd in lCmds:
      self.__send(lCmd)
      lOutput.extend(self.__expectprompt())
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
  # def setCurrentHwDevice(self, device):
      # return self.execute('current_hw_device {0}'.format(device))

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

