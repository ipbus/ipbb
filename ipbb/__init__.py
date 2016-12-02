from __future__ import print_function

from . import common

from os.path import join, split, exists, splitext, basename

#------------------------------------------------------------------------------
class Environment(object):
  """docstring for Environment"""
  def __init__(self):
    super(Environment, self).__init__()

    self._autodetect()

  def _autodetect(self):
    self.root = None
    self.rootFile = None
    self.project = None
    self.projectPath = None
    self.projectFile = None
    self.projectConfig = None


    lSignaturePath = common.findFileInParents( kSignatureFile )
    # 
    if lSignaturePath:
      self.root, self.rootFile = split( lSignaturePath )

    # 
    lProjectPath = common.findFileInParents( kProjectFile )

    if lProjectPath:
      self.projectPath, self.projectFile = split( lProjectPath )
      self.project = basename( self.projectPath )
      import json
      with open( lProjectPath,'r' ) as lProjectFile:
        self.projectConfig = json.load( lProjectFile )


  def __str__(self):
      return self.__repr__()+'''({{
  root: {root},
  project: {project},
  configuration: {projectConfig}
}})'''.format(**(self.__dict__))

  @property
  def src(self):
    return join(self.root, kSourceDir) if self.root is not None else None

  @property
  def work(self):
    return join(self.root, kWorkDir) if self.root is not None else None
#------------------------------------------------------------------------------

# Constants
kSignatureFile = '.ipbbarea'
kProjectFile = '.ipbbproj'
kSourceDir = 'source'
kWorkDir = 'work'