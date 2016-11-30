from __future__ import print_function
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import os
import sys
import subprocess

# #------------------------------------------------------------------------------
# # Helper function equivalent to which in posics systems
# def which( aExecutable ):
#   '''Searches for exectable il $PATH'''
#   return any(
#     os.access(os.path.join(lPath, aExecutable), os.X_OK) 
#     for lPath in os.environ["PATH"].split(os.pathsep)
#   )
# #------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Helper function equivalent to which in posics systems
def which( aExecutable ):
  '''Searches for exectable il $PATH'''
  for lPath in os.environ["PATH"].split(os.pathsep):
    if not os.access(os.path.join(lPath, aExecutable), os.X_OK): continue
    return os.path.normpath(os.path.join(lPath, aExecutable))
  return None
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def do( aCmdList  ):

  if isinstance(aCmdList, str):
    aCmdList = aCmdList.split('\n')

  for lCmd in aCmdList:
    print (lCmd)
    subprocess.check_call(lCmd, shell=True)      
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
       
  def __call__( self , string = "" ):
    self.file.write( string )
    self.file.write( "\n" )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def makeParser(env, verbosity ):
  from dep2g.Pathmaker import Pathmaker
  from dep2g.DepFileParser import DepFileParser

  lCfg = env.workConfig

  class dummy:pass
  lCommandLineArgs = dummy()
  lCommandLineArgs.define = ''
  lCommandLineArgs.product = lCfg['product']
  lCommandLineArgs.verbosity = verbosity


  lPathmaker = Pathmaker( env.src, verbosity )
  lDepFileParser = DepFileParser( lCommandLineArgs , lPathmaker )
  lDepFileParser.parse(lCfg['topPkg'], lCfg['topCmp'], lCfg['topDep'])

  return lDepFileParser, lPathmaker, lCommandLineArgs

#------------------------------------------------------------------------------