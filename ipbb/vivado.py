# Modules
import click
import os
import ipbb.env

# Elements
from os.path import join, split, exists, splitext
from ipbb.env import current as env

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

def create(workarea, component, dep):
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
  # lTopDepPath = join(env.src, lTopPackage, lTopComponent)
  lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', dep)
  if not exists(lTopDepPath):
    raise click.ClickException('Top-level dependency file %s not found' % lTopDepPath)
  #------------------------------------------------------------------------------

  # Build source code directory
  os.makedirs(lWorkAreaPath)

  lCfg = {
    'type': 'vivado',
    'topPkg': lTopPackage,
    'topCmp': lTopComponent,
    'topDep': dep,

  }
  with open(join(lWorkAreaPath,ipbb.env.kWorkFileName),'w') as lWorkFile:
    import json
    json.dump(lCfg, lWorkFile, indent=2)
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
@vivado.command()
def project():

  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  if env.workConfig['type'] != 'vivado':
    raise click.ClickException('Work area type mismatch. Expected \'vivado\', found \'%s\'' % env.workConfig['type'] )


  #------------------------------------------------------------------------------
  # Very messy, to be sorted out later
  from dep2g.Pathmaker import Pathmaker
  from dep2g.DepFileParser import DepFileParser

  class dummy:pass
  lCommandLineArgs = dummy()
  lCommandLineArgs.define = ''
  lCommandLineArgs.product = 'vivado'
  lCommandLineArgs.verbosity = 3
  lCommandLineArgs.output = ''

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
def build():
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  if env.workConfig['type'] != 'vivado':
    raise click.ClickException('Work area type mismatch. Expected \'vivado\', found \'%s\'' % env.workConfig['type'] )

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
def bitfile():
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  if env.workConfig['type'] != 'vivado':
    raise click.ClickException('Work area type mismatch. Expected \'vivado\', found \'%s\'' % env.workConfig['type'] )

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
def reset():
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  if env.workConfig['type'] != 'vivado':
    raise click.ClickException('Work area type mismatch. Expected \'vivado\', found \'%s\'' % env.workConfig['type'] )
  
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
