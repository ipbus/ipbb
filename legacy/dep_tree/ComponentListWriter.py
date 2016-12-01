from __future__ import print_function
import time, os

from SmartOpen import SmartOpen
from DepFileParser import DepFileParser
from CommandLineParser import CommandLineParser
from Pathmaker import Pathmaker

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ComponentListWriter( object ):
  def __init__( self , aCommandLineArgs , aPathmaker ):
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker
 
  def write( self , aScriptVariables , aComponentPaths , aCommandList , aLibs ):
    with SmartOpen( self.CommandLineArgs.output ) as write:
      for lComponentPath in aComponentPaths:
        write( self.Pathmaker.getpath( lComponentPath ) )


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
