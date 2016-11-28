from __future__ import print_function
#------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import sys

# Elements
from os.path import join, split, exists, splitext
from .common import which


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
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@sim.command()
@click.pass_obj
def project(env):
    
  if not which('vsim'):
    raise ModelsimNotFoundError('\'vsim\' not found in PATH.')
#------------------------------------------------------------------------------

