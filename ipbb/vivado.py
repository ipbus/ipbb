from __future__ import print_function

# Modules
import click
import os
import ipbb
# Elements
from os.path import join, split, exists, splitext

#------------------------------------------------------------------------------
def ensureVivado( env ):
  if env.workConfig['product'] != 'vivado':
    raise click.ClickException('Work area product mismatch. Expected \'vivado\', found \'%s\'' % env.workConfig['product'] )

  if 'XILINX_VIVADO' not in os.environ:
    raise click.ClickException('Vivado is not available. Have you sourced the environment script?' )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.group()
def vivado():
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
def validateCmp(ctx, param, value):
  lSeparators = value.count(':')
  # Validate the format
  if lSeparators > 1:
    raise click.BadParameter('Malformed component name : %s. Expected <module>:<component>' % value)
  
  return tuple(value.split(':'))


@vivado.command()
@click.argument('workarea')
@click.argument('component', callback=validateCmp)
@click.argument('dep')
@click.pass_obj
def create( env, workarea, component, dep ):
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
  lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', dep)
  if not exists(lTopDepPath):
    raise click.ClickException('Top-level dependency file %s not found' % lTopDepPath)
  #------------------------------------------------------------------------------

  # Build source code directory
  os.makedirs(lWorkAreaPath)

  lCfg = {
    'product': 'vivado',
    'topPkg': lTopPackage,
    'topCmp': lTopComponent,
    'topDep': dep,

  }
  with open(join(lWorkAreaPath,ipbb.kWorkFileName),'w') as lWorkFile:
    import json
    json.dump(lCfg, lWorkFile, indent=2)
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def project( env ):

  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  ensureVivado( env )
  
  #------------------------------------------------------------------------------
  # Very messy, to be sorted out later
  from dep2g.Pathmaker import Pathmaker
  from dep2g.DepFileParser import DepFileParser

  class dummy:pass
  lCommandLineArgs = dummy()
  lCommandLineArgs.define = ''
  lCommandLineArgs.product = lCfg['product']
  lCommandLineArgs.verbosity = 3
  # lCommandLineArgs.output = ''

  lPathmaker = Pathmaker(env.src, 0)

  lCfg = env.workConfig
  lDepFileParser = DepFileParser( lCommandLineArgs , lPathmaker )
  lDepFileParser.parse(lCfg['topPkg'], lCfg['topCmp'], lCfg['topDep'])

  from dep2g.VivadoProjectMaker import VivadoProjectMaker
  lWriter = VivadoProjectMaker(lCommandLineArgs, lPathmaker)

  import xilinx.vivado
  with xilinx.vivado.SmartConsole() as lTarget:
    lWriter.write(lTarget,lDepFileParser.ScriptVariables, lDepFileParser.Components, lDepFileParser.CommandList, None, None)

  #------------------------------------------------------------------------------
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def build( env ):
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  ensureVivado( env )

  lOpenCmds = [
    'open_project %s' % join(env.work, 'top', 'top'),
  ]

  lSynthCmds = [
    'launch_runs synth_1',
    'wait_on_run synth_1',
  ]

  lImplCmds = [
    'launch_runs impl_1',
    'wait_on_run impl_1',
  ]

  lBitFileCmds = [
    'launch_runs impl_1 -to_step write_bitstream',
    'wait_on_run impl_1',
  ]

  import xilinx.vivado
  with xilinx.vivado.SmartConsole() as lTarget:
    lTarget(lOpenCmds)
    lTarget(lSynthCmds)
    lTarget(lImplCmds)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def bitfile( env ):
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  ensureVivado( env )

  lOpenCmds = [
    'open_project %s' % join(env.work, 'top', 'top'),
  ]

  lBitFileCmds = [
    'launch_runs impl_1 -to_step write_bitstream',
    'wait_on_run impl_1',
  ]

  import xilinx.vivado
  with xilinx.vivado.SmartConsole() as lTarget:
    lTarget(lOpenCmds)
    lTarget(lBitFileCmds)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def reset( env ):
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  ensureVivado( env )

  lOpenCmds = [
    'open_project %s' % join(env.work, 'top', 'top'),
  ]

  lResetCmds = [
    'reset_run synth_1',
    'reset_run impl_1',
  ]

  import xilinx.vivado
  with xilinx.vivado.SmartConsole() as lTarget:
    lTarget(lOpenCmds)
    lTarget(lResetCmds)
#------------------------------------------------------------------------------
