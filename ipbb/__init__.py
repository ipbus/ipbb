from __future__ import print_function

from . import common

from os.path import join, split, exists, splitext

#------------------------------------------------------------------------------
class Environment(object):
  """docstring for Environment"""
  def __init__(self):
    super(Environment, self).__init__()

    self._autodetect()

  def _autodetect(self):
    self.root = None
    self.rootFile = None
    self.work = None
    self.workFile = None
    self.workConfig = None
    lBuildFilePath = common.findFileInParents(kBuildFileName)
    lWorkFilePath = common.findFileInParents(kWorkFileName)

    if lBuildFilePath:
      self.root, self.rootFile = split( lBuildFilePath )

    if lWorkFilePath:
      self.work, self.workFile = split( lWorkFilePath )
      import json
      with open(lWorkFilePath,'r') as lWorkFile:
        self.workConfig = json.load(lWorkFile)


  def __str__(self):
      return '{{ root: {root}, work: {work}, work_cfg: {workConfig} }}'.format(**(self.__dict__))

  @property
  def src(self):
    return join(self.root, kSourceDir) if self.root is not None else None
#------------------------------------------------------------------------------

# Constants
kBuildFileName = '.buildarea'
kWorkFileName = '.workarea'
kSourceDir = 'src'
