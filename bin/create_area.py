#!/bin/env python

from __future__ import print_function

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class DirSentry:

  def __init__(self, aDir):
    self.dir = aDir

  def __enter__(self):
    if not os.path.exists(self.dir):
        raise RuntimeError('stocazzo '+self.dir)

    self._lOldDir = os.path.realpath(os.getcwd())
    # print self._lOldDir
    os.chdir(self.dir)
    return self 

  def __exit__(self, type, value, traceback):
    os.chdir(self._lOldDir)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


repoPath = 'https://:@gitlab.cern.ch:8443/ipbus/dummy-fw-proj.git'

from os.path import join, split, exists
import os
import subprocess

kSignatureFile = '.build'
kSourceDir = 'src'

subprocess.call(['rm','-rf',kSignatureFile, kSourceDir])

def findBuildFile():
  lPath = os.getcwd()

  # import pdb; pdb.set_trace()

  while lPath is not '/':
    lBuildFile = join(lPath,kSignatureFile)
    if exists(lBuildFile):
      return lBuildFile
    lPath,_ = split(lPath)

  return None

lBuildFile = findBuildFile()
if lBuildFile is not None:
  raise SystemExit('Buildfile already exists',lBuildFile)

if exists(kSourceDir):
  raise SystemExit('Source directory \'src\' already exists')

with open(kSignatureFile,'w') as lBuild:
  lBuild.write('\n')

# Build source code directory
os.mkdir(kSourceDir)

with DirSentry('src') as lSentry:
  subprocess.check_call(['git','clone',repoPath])

