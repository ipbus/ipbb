from __future__ import print_function
import time, os

from SmartOpen import SmartOpen
from DepFileParser import DepFileParser
from CommandLineParser import CommandLineParser
from Pathmaker import Pathmaker

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class AddressTableListWriter( object ):
  def __init__( self , aCommandLineArgs , aPathmaker ):
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker
 
  def write( self , aScriptVariables , aComponentPaths , aCommandList , aLibs, aMaps ):
    with SmartOpen( self.CommandLineArgs.output ) as write:
      for addrtab in aCommandList["addrtab"]:
        write( addrtab.FilePath )

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
