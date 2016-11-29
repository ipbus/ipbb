from __future__ import print_function
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import os
import sys

#------------------------------------------------------------------------------
# Helper function equivalent to which in posics systems
def which( aExecutable ):
  '''Searches for exectable il $PATH'''
  return any(
    os.access(os.path.join(lPath, aExecutable), os.X_OK) 
    for lPath in os.environ["PATH"].split(os.pathsep)
  )
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
