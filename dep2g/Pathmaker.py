from __future__ import print_function
import os

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Pathmaker(object):

  fpaths = {"src": "firmware/hdl", "include": "firmware/cfg", "addrtab": "addr_table", "setup": "firmware/cfg"}
  fexts = {"src": "vhd", "include": "dep", "addrtab": "xml" } #, "setup": "tcl"}

  #--------------------------------------------------------------
  def __init__(self, rootdir, verbosity):
    self.rootdir = rootdir
    self.verbosity = verbosity

    if self.verbosity > 3:
      print("+++ Pathmaker init", rootdir)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getPackagePath(self, aPackage):
    return os.path.normpath( os.path.join( self.rootdir, aPackage ) )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def packageExists( self, aPackage ):
    return os.path.exists( self.getPackagePath(aPackage) )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getPath( self, package, component=None, kind=None, name=None, cd=None):

    # path = [package, component]
    path = [package]

    if component:
      path.append( component )

    if kind:
      path.append( self.fpaths[kind] )

    if cd:
      path.append( cd )

    if name:
        path.append( name )

    lPath = os.path.normpath( os.path.join( self.rootdir, *path ) )

    if self.verbosity > 2:
      print('+++ Pathmaker', package, component, kind, name, cd)
    return lPath
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getDefName(self, kind, name):
    return "{0}.{1}".format( name , self.fexts[kind] )
  #--------------------------------------------------------------
  

  #--------------------------------------------------------------
  def glob( self, package, component, kind, fileexpr, cd = None ):
    import glob

    lPathExpr = self.getPath( package, component, kind , fileexpr , cd = cd )
    lComponentPath = self.getPath( package, component, kind , cd = cd )
    lFilePaths = glob.glob( lPathExpr )
    # Calculate the relative path and pair it up with the absolute path
    lFileList = [ (os.path.relpath( lPath2, lComponentPath ),lPath2) for lPath2 in lFilePaths ]
    return  lPathExpr, lFileList
  #--------------------------------------------------------------

