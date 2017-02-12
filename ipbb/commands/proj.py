from __future__ import print_function

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from . import kProjectFileName, kWorkDir
from .common import DirSentry

from os.path import join, split, exists, splitext
from ..tools.common import SmartOpen


#------------------------------------------------------------------------------
def _getprojects(env):

  if not exists(env.work):
    raise click.ClickException("Directory '%s' does not exist." % env.work )

  '''Returns the list of existing projects'''
  return [ lArea for lArea in next(os.walk(env.work))[1] if exists( join( env.work, lArea, kProjectFileName ) ) ]
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.group()
def proj():
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def _validateComponent(ctx, param, value):
  lSeparators = value.count(':')
  # Validate the format
  if lSeparators > 1:
    raise click.BadParameter('Malformed component name : %s. Expected <module>:<component>' % value)
  
  return tuple(value.split(':'))
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# TODO: move the list of supported products somewhere else
@proj.command()
@click.argument('kind', type=click.Choice(['vivado', 'sim']))
@click.argument('projarea')
@click.argument('component', callback=_validateComponent)
@click.option('-t', '--topdep', default='top.dep', help='Top-level dependency file')
@click.pass_obj
def create( env, kind, projarea, component, topdep ):
  '''Create a new project area

    
    Creates a new area of name PROJAREA of kind KIND 

    PROJAREA: bbb
    
    COMPONENT: cc 
  '''
  #------------------------------------------------------------------------------
  # Must be in a build area
  if env.root is None:
    raise click.ClickException('Build area root directory not found')
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  lProjAreaPath = join( env.root, kWorkDir, projarea )
  if exists(lProjAreaPath):
    raise click.ClickException('Directory %s already exists' % lProjAreaPath)
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  from ..dep2g.Pathmaker import Pathmaker
  lPathmaker = Pathmaker(env.src, 0)
  lTopPackage, lTopComponent = component
  lTopDepPath = lPathmaker.getPath( lTopPackage, lTopComponent, 'include', topdep )
  if not exists(lTopDepPath):
    raise click.ClickException('Top-level dependency file %s not found' % lTopDepPath)
  #------------------------------------------------------------------------------

  # Build source code directory
  os.makedirs(lProjAreaPath)

  lCfg = {
    'toolset': kind,
    'topPkg': lTopPackage,
    'topCmp': lTopComponent,
    'topDep': topdep,
    'name': projarea

  }
  with SmartOpen( join(lProjAreaPath, kProjectFileName) ) as lProjFile:
    import json
    json.dump(lCfg, lProjFile.file, indent=2)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@proj.command()
@click.pass_obj
def ls( env ):
  lProjects = _getprojects(env)
  print ( 'Root:', env.root )
  print ( 'Projects areas:', ', '.join( [ lProject + ('*' if lProject == env.project else '') for lProject in lProjects ] ) )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@proj.command()
@click.argument( 'proj' )
@click.pass_obj
def cd(env,proj):

  if proj[-1] == os.sep: proj = proj[:-1]
  lProjects = _getprojects(env)
  if proj not in lProjects:
    raise click.ClickException('Requested work area not found. Available areas %s' % ', '.join(lProjects))

  with DirSentry( join(env.work,proj) ) as lSentry:
    env._autodetect()

  os.chdir(join(env.work,proj))
  print( 'New current directory %s' % os.getcwd() )
#------------------------------------------------------------------------------
