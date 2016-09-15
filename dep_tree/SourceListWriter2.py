from __future__ import print_function
import time, os, subprocess

from SmartOpen import SmartOpen
from DepFileParser import DepFileParser
from CommandLineParser import CommandLineParser
from Pathmaker import Pathmaker


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def SvnStatus( file , root ):
  status = dict()
  
  process = subprocess.Popen( [ "svn" , "status" , "-v" , file ] , stdout=subprocess.PIPE , stderr=subprocess.PIPE )
  out, err = process.communicate()
          
  status[ 'Name' ] = os.path.relpath( file , root )

  flags = out[0:7]
  out = out[7:]
  
  if flags[0] != " " : status[ 'SvnFileStatus' ] = flags[0]
  if flags[1] != " " : status[ 'SvnProperties' ] = flags[1]
  if flags[2] != " " : status[ 'SvnLocked' ] = flags[2]
  if flags[3] != " " : status[ 'SvnAdditionScheduled' ] = flags[3]
  if flags[4] != " " : status[ 'SvnItemSwitched' ] = flags[4]
  if flags[5] != " " : status[ 'SvnRepositoryLock' ] = flags[5]
  if flags[6] != " " : status[ 'SvnTreeConflict' ] = flags[6]
    
  if flags[6] == 'C': #Tree conflict adds an additional information line
    out , conflict =  out.split( '\n' )
    status[ 'Conflict' ] = conflict.strip( " \r\n\t<>" )

  properties = out.split()
  
  if len(properties) >= 4:
    status[ 'CheckOutRevision' ] = properties[-4]
    status[ 'CommitRevision' ] = properties[-3]
    status[ 'LastModAuthor' ] = properties[-2]
    
  return status

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class SourceListWriter2( object ):
  def __init__( self , aCommandLineArgs , aPathmaker ):
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker
 
  def write( self , aScriptVariables , aComponentPaths , aCommandList , aLibs, aMaps ):
    with SmartOpen( self.CommandLineArgs.output ) as write:
      write( "<FileList>" )
    
      for src in aCommandList["src"]:
        status = SvnStatus( src.FilePath , self.Pathmaker.root )
        string = [ '{0}="{1}"'.format(key,val).ljust(24) for key,val in sorted(status.iteritems()) ]
        write( "  <File {0} />".format( " ".join( string ) ) )
  
      write( "</FileList>" )

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

