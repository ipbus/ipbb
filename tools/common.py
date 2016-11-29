from __future__ import print_function
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
import os

#------------------------------------------------------------------------------
# Helper function equivalent to which in posics systems
def which( aExecutable ):
  '''Searches for exectable il $PATH'''
  return any(
    os.access(os.path.join(lPath, aExecutable), os.X_OK) 
    for lPath in os.environ["PATH"].split(os.pathsep)
  )
#------------------------------------------------------------------------------
