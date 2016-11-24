from __future__ import print_function
import time, os

from DepFileParser import DepFileParser

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class AddressTableListMaker( object ):
  def __init__( self , aCommandLineArgs , aPathmaker ):
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker
 
  def write( self , aTarget, aScriptVariables , aComponentPaths , aCommandList , aLibs, aMaps ):

    write = aTarget

    for addrtab in aCommandList["addrtab"]:
      write( addrtab.FilePath )

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
