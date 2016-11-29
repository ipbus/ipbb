from __future__ import print_function
#------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from os.path import join, split, exists, splitext, basename
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
# FIXME: duplicated in vivado.create
def _validateComponent(ctx, param, value):
  lSeparators = value.count(':')
  # Validate the format
  if lSeparators > 1:
    raise click.BadParameter('Malformed component name : %s. Expected <module>:<component>' % value)
  
  return tuple(value.split(':'))


@sim.command()
@click.argument('workarea')
@click.argument('component', callback=_validateComponent)
@click.option('-t', '--topdep', default='top.dep', help='Top-level dependency file')
@click.pass_obj
def create( env, workarea, component, topdep ):
  '''Create a new ModelSim/QuestaSim working area'''
  #------------------------------------------------------------------------------
  # Must be in a build area
  if env.root is None:
    raise click.ClickException('Build area root directory not found')
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  lWorkAreaPath = join(env.root, workarea)
  if exists(lWorkAreaPath):
    raise click.ClickException('Directory %s already exists' % lWorkAreaPath)
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  from dep2g.Pathmaker import Pathmaker
  lPathmaker = Pathmaker(env.src, 0)
  lTopPackage, lTopComponent = component
  lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', topdep)
  if not exists(lTopDepPath):
    raise click.ClickException('Top-level dependency file %s not found' % lTopDepPath)
  #------------------------------------------------------------------------------

  # Build source code directory
  os.makedirs(lWorkAreaPath)

  lCfg = {
    'product': 'sim',
    'topPkg': lTopPackage,
    'topCmp': lTopComponent,
    'topDep': topdep,

  }
  with open(join(lWorkAreaPath,ipbb.kWorkFileName),'w') as lWorkFile:
    import json
    json.dump(lCfg, lWorkFile, indent=2)

#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@sim.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def ipcores(env, output):

  #------------------------------------------------------------------------------
  # Must be in a build area
  if env.work is None:
    raise click.ClickException('Work area root directory not found')
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  if not which('vivado'):
  # if 'XILINX_VIVADO' not in os.environ:
    raise click.ClickException('Vivado is not available. Have you sourced the environment script?' )
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  # Very messy, to be sorted out later
  from dep2g.Pathmaker import Pathmaker
  from dep2g.DepFileParser import DepFileParser

  lCfg = env.workConfig

  class dummy:pass
  lCommandLineArgs = dummy()
  lCommandLineArgs.define = ''
  lCommandLineArgs.product = lCfg['product']
  lCommandLineArgs.verbosity = 3

  lPathmaker = Pathmaker(env.src, 0)

  lDepFileParser = DepFileParser( lCommandLineArgs , lPathmaker )
  lDepFileParser.parse(lCfg['topPkg'], lCfg['topCmp'], lCfg['topDep'])


  from dep2g.IPCoresSimMaker import IPCoresSimMaker
  lWriter = IPCoresSimMaker(lCommandLineArgs, lPathmaker)

  # Yeah, this is a hack
  os.environ['XILINX_SIMLIBS'] = join('.xil_sim_libs',basename(os.environ['XILINX_VIVADO']))

  if output:
    from dep_tree.SmartOpen import SmartOpen
    with SmartOpen(output) as lTarget:
      lWriter.write(lTarget,lDepFileParser.ScriptVariables, lDepFileParser.Components, lDepFileParser.CommandList , lDepFileParser.Libs, lDepFileParser.Maps)
  else:
    import tools.xilinx
    with tools.xilinx.VivadoOpen() as lTarget:
      lWriter.write(lTarget,lDepFileParser.ScriptVariables, lDepFileParser.Components, lDepFileParser.CommandList , lDepFileParser.Libs, lDepFileParser.Maps)
#------------------------------------------------------------------------------

