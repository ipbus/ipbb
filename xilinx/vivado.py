import logging
import pexpect
import sys
import collections

class Vivado(object):
  """docstring for Vivado"""
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
  def __expectprompt(self):
    index = None
    buffer = []
    while True:
      # Search for newlines, prompt, end-of-file
      # index = self._me.expect(['\r\n','Vivado%\t', 'ERROR:', pexpect.EOF])
      index = self._me.expect(['\r\n','Vivado%\t', 'ERROR:'])
      # print '>',self._me.before

      # Break if prompt or EOF
      if index != 0:
        break

      # Store the 
      buffer += [self._me.before]

    return buffer
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __send(self, text):
    self._me.sendline(text)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def __run(self, text):

    import re
    char_backspace = re.compile(".\b")
    
    self.__send(text)
    output = self.__expectprompt()

    # Sanitise Vivado output (backspaces leaking in here?!?)
    cmdrcvd = char_backspace.sub('',output[0])
    cmdsent = text
    if cmdrcvd != cmdsent:
        #-----
        # Find where the 2 strings don't match
        print len(cmdrcvd), len(cmdsent)
        for i in xrange(min(len(cmdrcvd), len(cmdsent))):
            r = cmdrcvd[i]
            s = cmdsent[i]
            # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s), ord(s) > 128 
            print i, '\t', r, s, r==s, ord(r)

        print ''.join([str(i%10) for i in xrange(len(cmdrcvd))])
        print cmdrcvd
        print ''.join([str(i%10) for i in xrange(len(cmdsent))])
        print cmdsent
        #-----
        #
        raise RuntimeError('Command and first output line don\'t match cmdsent=\'{0}\', cmdrcvd=\'{1}\''.format(cmdsent,cmdrcvd))
    return output[1:]
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def execute(self, text):
    if isinstance(text, str):
      cmds = [text]
    elif isinstance(text, list):
      cmds = text

    output = []
    for cmd in cmds:
      output.append(self.__run(cmd))
    return output
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

