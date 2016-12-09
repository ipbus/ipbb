from __future__ import print_function

from . import common

from os import walk
from os.path import join, split, exists, splitext, basename
from dep2g.Pathmaker import Pathmaker
from dep2g.DepFileParser import DepFileParser

#------------------------------------------------------------------------------
class Environment(object):
  """docstring for Environment"""

  _verbosity = 0

  #------------------------------------------------------------------------------
  def __init__(self):
    super(Environment, self).__init__()

    self._autodetect()
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  def _clear(self):
    self.root = None
    self.rootFile = None
    
    self.project = None
    self.projectPath = None
    self.projectFile = None
    self.projectConfig = None

    self.pathMaker = None
    self.depParser = None
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  def _autodetect(self):

    self._clear()

    lSignaturePath = common.findFileInParents( kSignatureFile )

    # Stop here is no signature is found 
    if not lSignaturePath:
      return

    self.root, self.rootFile = split( lSignaturePath )
    self.pathMaker = Pathmaker( self.src, self._verbosity )

    lProjectPath = common.findFileInParents( kProjectFile )

    # Stop here if no project file is found
    if not lProjectPath:
      return

    self.projectPath, self.projectFile = split( lProjectPath )
    self.project = basename( self.projectPath )
    import json
    with open( lProjectPath,'r' ) as lProjectFile:
      self.projectConfig = json.load( lProjectFile )

    #------------------------------------------------------------------------------
    class dummy:pass
    lCommandLineArgs = dummy()
    lCommandLineArgs.define = ''
    lCommandLineArgs.product = self.projectConfig['product']
    lCommandLineArgs.verbosity = self._verbosity
    #------------------------------------------------------------------------------


    lPathmaker = Pathmaker( self.src, self._verbosity )
    self.depParser = DepFileParser( lCommandLineArgs , self.pathMaker )
    self.depParser.parse(
      self.projectConfig['topPkg'],
      self.projectConfig['topCmp'],
      self.projectConfig['topDep']
    )
  #------------------------------------------------------------------------------


  #------------------------------------------------------------------------------
  def __str__(self):
      return self.__repr__()+'''({{
  root: {root},
  project: {project},
  configuration: {projectConfig},
  pathMaker: {pathMaker},
  parser: {depParser}
}})'''.format(**(self.__dict__))
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  @property
  def src(self):
    return join(self.root, kSourceDir) if self.root is not None else None
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  @property
  def work(self):
    return join(self.root, kWorkDir) if self.root is not None else None
  #------------------------------------------------------------------------------
  
  #------------------------------------------------------------------------------
  def getsources(self):
    return next(walk(self.src))[1]
  #------------------------------------------------------------------------------
  
  #------------------------------------------------------------------------------
  def getworks(self):
    return [ lProj for lProj in next(walk(self.work))[1] if exists( join( self.work, lProj, kProjectFile ) ) ]
  #------------------------------------------------------------------------------

#------------------------------------------------------------------------------

# Constants
kSignatureFile = '.ipbbarea'
kProjectFile = '.ipbbproj'
kSourceDir = 'source'
kWorkDir = 'work'