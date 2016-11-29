from __future__ import print_function
#------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from os.path import join, split, exists, splitext
from tools.common import which


#------------------------------------------------
class ModelsimNotFoundError(Exception):

  def __init__(self, message):
    # Call the base class constructor with the parameters it needs
    super(ModelsimNotFoundError, self).__init__(message)
#------------------------------------------------


#------------------------------------------------------------------------------
@click.group()
def sim():
    pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@sim.command()
@click.pass_obj
def create(env):
  if not which('vsim'):
    raise ModelsimNotFoundError('\'vsim\' not found in PATH.')

  lVsim = subprocess.Popen(['vsim','-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = lVsim.communicate()

  if lVsim.returncode != 0:
    raise RuntimeError()

  print (out.strip())

#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@sim.command()
@click.pass_obj
def project(env):
    
  if not which('vsim'):
    raise ModelsimNotFoundError('\'vsim\' not found in PATH.')
#------------------------------------------------------------------------------

