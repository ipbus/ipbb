from __future__ import print_function
import time, os

from SmartOpen import SmartOpen
from DepFileParser import DepFileParser
from CommandLineParser import CommandLineParser
from Pathmaker import Pathmaker

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class SourceListWriter( object ):
  def __init__( self , aCommandLineArgs , aPathmaker ):
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker
 
  def write( self , aScriptVariables , aComponentPaths , aCommandList , aLibs, aMaps ):
    with SmartOpen( self.CommandLineArgs.output ) as write:
      for src in aCommandList["src"]:
        if src.Include:
          write( src.FilePath )  


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
