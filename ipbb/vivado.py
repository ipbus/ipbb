from __future__ import print_function
#------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
# Elements
from os.path import join, split, exists, splitext
from tools.common import which, makeParser

#------------------------------------------------------------------------------
def ensureVivado( env ):
  if env.workConfig['product'] != 'vivado':
    raise click.ClickException("Work area product mismatch. Expected 'vivado', found '%s'" % env.workConfig['product'] )

  if not which('vivado'):
  # if 'XILINX_VIVADO' not in os.environ:
    raise click.ClickException("Vivado is not available. Have you sourced the environment script?" )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.group() # chain = True
def vivado():
  '''Vivado command group'''
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# FIXME: duplicated in sim.create
def _validateComponent(ctx, param, value):
  lSeparators = value.count(':')
  # Validate the format
  if lSeparators > 1:
    raise click.BadParameter('Malformed component name : %s. Expected <module>:<component>' % value)
  
  return tuple(value.split(':'))


@vivado.command()
@click.argument('workarea')
@click.argument('component', callback=_validateComponent)
@click.option('-t', '--topdep', default='top.dep', help='Top-level dependency file')
@click.pass_obj
def create( env, workarea, component, topdep ):
  '''Create a new Vivado working area'''
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
    'product': 'vivado',
    'topPkg': lTopPackage,
    'topCmp': lTopComponent,
    'topDep': topdep,

  }
  with open(join(lWorkAreaPath,ipbb.kWorkFileName),'w') as lWorkFile:
    import json
    json.dump(lCfg, lWorkFile, indent=2)
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def project( env ):
  '''Assemble current vivado project'''
  
  if env.work is None:
    raise click.ClickException('Work area root directory not found')

  ensureVivado( env )
  
  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser( env, 3 )

  from dep2g.VivadoProjectMaker import VivadoProjectMaker
  lWriter = VivadoProjectMaker(lCommandLineArgs, lPathmaker)

  import tools.xilinx
  with tools.xilinx.VivadoOpen() as lTarget:
    lWriter.write(lTarget,lDepFileParser.ScriptVariables, lDepFileParser.Components, lDepFileParser.CommandList , lDepFileParser.Libs, lDepFileParser.Maps)
  #------------------------------------------------------------------------------
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def build( env ):
  '''Syntesize and implement current vivado project'''

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

  import tools.xilinx
  with tools.xilinx.VivadoOpen() as lTarget:
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

  import tools.xilinx
  with tools.xilinx.VivadoOpen() as lTarget:
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

  import tools.xilinx
  with tools.xilinx.VivadoOpen() as lTarget:
    lTarget(lOpenCmds)
    lTarget(lResetCmds)
#------------------------------------------------------------------------------
