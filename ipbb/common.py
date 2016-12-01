from __future__ import print_function
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
import os

#------------------------------------------------------------------------------
class DirSentry:
  def __init__(self, aDir):
    self.dir = aDir

  def __enter__(self):
    if not os.path.exists(self.dir):
        raise RuntimeError('Directory '+self.dir+' does not exist')

    self._lOldDir = os.path.realpath(os.getcwd())
    # print self._lOldDir
    os.chdir(self.dir)
    return self 

  def __exit__(self, type, value, traceback):
    import os
    os.chdir(self._lOldDir)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def findFileInParents(aAreaFileName):
  lPath = os.getcwd()

  while lPath is not '/':
    lBuildFile = os.path.join(lPath,aAreaFileName)
    if os.path.exists(lBuildFile):
      return lBuildFile
    lPath,_ = os.path.split(lPath)

  return None
#------------------------------------------------------------------------------