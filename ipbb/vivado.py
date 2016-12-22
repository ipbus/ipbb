from __future__ import print_function
#------------------------------------------------------------------------------

# Modules
import click
import os
import ipbb
# Elements
from os.path import join, split, exists, splitext, abspath, basename
from tools.common import which, SmartOpen
from .common import DirSentry

#------------------------------------------------------------------------------
def ensureVivado( env ):
  if env.projectConfig['toolset'] != 'vivado':
    raise click.ClickException("Work area product mismatch. Expected 'vivado', found '%s'" % env.projectConfig['toolset'] )

  if not which('vivado'):
  # if 'XILINX_VIVADO' not in os.environ:
    raise click.ClickException("Vivado is not available. Have you sourced the environment script?" )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.group( chain = True )
def vivado():
  '''Vivado command group'''
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@vivado.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def project( env, output ):
  '''Assemble current vivado project'''

  if env.project is None:
    raise click.ClickException('Project area not defined. Move into a project area and try again')

  ensureVivado( env )

  # lDepFileParser, lPathmaker, lCommandLineArgs = makeParser( env, 3 )
  lDepFileParser = env.depParser

  from dep2g.VivadoProjectMaker import VivadoProjectMaker
  lWriter = VivadoProjectMaker( env.pathMaker )

  from tools.xilinx import VivadoOpen
  with ( VivadoOpen() if not output else SmartOpen( output if output != 'stdout' else None ) ) as lTarget:
    lWriter.write(
      lTarget,
      lDepFileParser.ScriptVariables,
      lDepFileParser.Components,
      lDepFileParser.CommandList ,
      lDepFileParser.Libs,
      lDepFileParser.Maps
    )
  #------------------------------------------------------------------------------
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def build( env ):
  '''Syntesize and implement current vivado project'''

  if env.project is None:
    raise click.ClickException('Project area not defined. Move into a project area and try again')

  ensureVivado( env )

  lOpenCmds = [
    'open_project %s' % join(env.projectPath, 'top', 'top'),
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
  if env.project is None:
    raise click.ClickException('Project area not defined. Move into a project area and try again')

  ensureVivado( env )

  lOpenCmds = [
    'open_project %s' % join(env.projectPath, 'top', 'top'),
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
  if env.project is None:
    raise click.ClickException('Project area not defined. Move into a project area and try again')

  ensureVivado( env )

  lOpenCmds = [
    'open_project %s' % join(env.project, 'top', 'top'),
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

#------------------------------------------------------------------------------
@vivado.command()
@click.pass_obj
def package( env ):
  '''List address table files'''
  ensureVivado( env )

  lBitPath = join('top','top.runs','impl_1','top.bit')
  if not exists(lBitPath):
    raise ValueError("Bitfile {0} not found. Please run 'bitfile' command first.".format(lBitPath))

  import sh
  lPkgPath = 'package'
  lSrcPath = join(lPkgPath,'src')

  # Cleanup first
  sh.rm('-rf', lPkgPath)

  # Create the folders
  try: os.makedirs(join(lSrcPath,'addrtab'))
  except OSError as e: pass


  #------------------------------------------------------------------------------
  # Generate a json signature file
  import socket, time

  lSignature = dict(env.projectConfig)
  lSignature.update({
    'time': socket.gethostname().replace('.','_'),
    'build host': time.strftime("%a, %d %b %Y %H:%M:%S +0000"),
  })

  with SmartOpen(join(lSrcPath,'signature')) as lSignatureFile:
    import json
    json.dump(lSignature, lSignatureFile.file, indent=2)
  #------------------------------------------------------------------------------

  print( sh.cp( '-av', lBitPath, lSrcPath ) )

  # for addrtab in lDepFileParser.CommandList['addrtab']:
  for addrtab in env.depParser.CommandList['addrtab']:
    print( sh.cp( '-av', addrtab.FilePath, join(lSrcPath,'addrtab') ) )

  lTgzBaseName = '{name}_{host}_{time}'.format(
    name=env.projectConfig['name'],
    host=socket.gethostname().replace('.','_'),
    time=time.strftime('%y%m%d_%H%M')
    )
  lTgzPath = abspath(join(lPkgPath,lTgzBaseName+'.tgz'))

  # with DirSentry( lSrcPath ) as lSentry:
    # print ( os.getcwd() )
    # Zip it
  print(sh.tar('cvfz', lTgzPath, '-C', lPkgPath, '--transform', 's/^src/'+lTgzBaseName+'/', 'src'))
#------------------------------------------------------------------------------

