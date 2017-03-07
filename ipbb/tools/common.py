from __future__ import print_function
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import os
import sys
import pexpect
import subprocess

#------------------------------------------------------------------------------
# Helper function equivalent to which in posics systems
def which( aExecutable ):
  '''Searches for exectable il $PATH'''
  lSearchPaths = os.environ["PATH"].split(os.pathsep) if aExecutable[0] != os.sep else [os.path.dirname(aExecutable)]
  for lPath in lSearchPaths:
    if not os.access(os.path.join(lPath, aExecutable), os.X_OK): continue
    return os.path.normpath(os.path.join(lPath, aExecutable))
  return None
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# TODO: turn it into a class?
# Use 'sh' instead?
def do( aCmdList  ):

  if isinstance(aCmdList, str):
    aCmdList = aCmdList.split('\n')

  for lCmd in aCmdList:
    print (lCmd)
    subprocess.check_call(lCmd, shell=True)      
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def ensuresudo( ):
  import pexpect, getpass
  lPrompt = '> '

  p = pexpect.spawn('sudo -p "{0}" whoami'.format(lPrompt) ) #, logfile = sys.stdout)
  lIndex = p.expect([pexpect.EOF, lPrompt])

  # I have sudo powers, therefore I return
  while lIndex != 0:
    lPwd = getpass.getpass('Please insert password for user {0}: '.format(os.getlogin()))
    p.sendline(lPwd)
    lIndex = p.expect([pexpect.EOF, lPrompt])
    if lIndex == 0: break

  return p.exitstatus
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
class SmartOpen( object ):

  def __init__( self, aFilename=None ):
    self.filename = aFilename
    self.file = None
  
  def __enter__(self):
    if self.filename:
      print( "Writing to" , self.filename )
      self.file = open( self.filename, 'w')
    else:
      self.file = sys.stdout
    return self
  
  def __exit__(self ,type, value, traceback):
    if self.file is not sys.stdout:
      self.file.close()
       
  def __call__( self , *strings ):
    self.file.write( ' '.join( strings ) )
    self.file.write( "\n" )
#------------------------------------------------------------------------------
