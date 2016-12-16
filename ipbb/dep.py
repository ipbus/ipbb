from __future__ import print_function

# Modules
import click
import os
import sh

from os.path import join, split, exists, basename, abspath, splitext
from tools.common import which, SmartOpen
from .common import DirSentry

#------------------------------------------------------------------------------
@click.group()
def dep():
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def print( env, output ):
  '''Print the '''

  with SmartOpen( output ) as lWriter:
    lWriter( str( env.depParser ) )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.argument('group',type=click.Choice(['setup', 'src', 'addrtab', 'cgpfile']))
@click.option('-o', '--output', default=None)
@click.pass_obj
def ls( env, group, output ):
  '''List source files'''

  with SmartOpen( output ) as lWriter:
    for addrtab in env.depParser.CommandList[group]:
      lWriter( addrtab.FilePath )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-o', '--output', default='addrtab')
def addrtab( env, output ):
  '''Copy address table files into addrtab subfolder'''

  try:
    os.mkdir(output)
  except OSError as e:
    pass

  import sh
  for addrtab in env.depParser.CommandList["addrtab"]:
    print( sh.cp( '-av', addrtab.FilePath, join(output, basename(addrtab.FilePath) ) ) ) 
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def components( env, output ):

  # lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  with SmartOpen( output ) as lWriter:
    for lPkt, lCmps in env.depParser.Components.iteritems():
      lWriter('['+lPkt+']')
      for lCmp in lCmps:
        lWriter(lCmp)
      lWriter()
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
def status(env):
    pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------

import contextlib

@contextlib.contextmanager
def set_env( **environ ):
    """
    Temporarily set the process environment variables.

    >>> with set_env(PLUGINS_DIR=u'test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    lOldEnviron = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(lOldEnviron)

#----
@dep.command()
@click.pass_context
def generate( ctx ):
  
  lDecodersDir = 'decoders'
  # Extract context
  env = ctx.obj

  with DirSentry( env.projectPath ) as lProjDir:
    sh.rm('-rf', lDecodersDir)
    # Gather address tables
    ctx.invoke(addrtab, output=lDecodersDir)
  
  #------------------------------------------------------------------------------
  # TODO: Clean me up
  lGenScript = 'gen_ipbus_addr_decode'
  if not which(lGenScript):
    os.environ['PATH'] = '/opt/cactus/bin/uhal/tools:' + os.environ['PATH']
    if not which(lGenScript):
      raise click.ClickException("'{0}' script not found.".format(lGenScript))
  
  if '/opt/cactus/lib' not in os.environ['LD_LIBRARY_PATH'].split(':'):
    os.environ['LD_LIBRARY_PATH'] = '/opt/cactus/lib:' + os.environ['LD_LIBRARY_PATH']
  #------------------------------------------------------------------------------
  
  lUpdatedDecoders = []
  lGen = sh.Command(lGenScript)
  with DirSentry( join(env.projectPath, lDecodersDir) ) as lProjDir:
    for lAddr in env.depParser.CommandList['addrtab']:
      
      # Interested in top-level address tables only
      if not lAddr.TopLevel: continue

      # Generate a new decoder file
      lGen(basename(lAddr.FilePath))
      lDecoder = 'ipbus_decode_{0}.vhd'.format( splitext( basename( lAddr.FilePath ) )[0])
      lTarget = env.pathMaker.getPath(lAddr.Package, lAddr.Component, 'src', lDecoder )

      # Has anything changed?
      try:
        sh.diff( '-u', '-I', '^-- START automatically', lDecoder, lTarget  )
      except sh.ErrorReturnCode as e:
        print ( e.stdout )

        lUpdatedDecoders.append( (lDecoder, lTarget) )

    #------------------------------------------------------------------------------
    # If no difference between old and newly generated decoders, quit here.
    if not lUpdatedDecoders:
      print ( 'All ipbus decoders are up-to-date' )
      return
    #------------------------------------------------------------------------------

    print ( 'The following decoders have changed:\n' +'\n'.join([ '* '+lDecoder for lDecoder,lTarget in lUpdatedDecoders] ) )
    click.confirm('Do you want to continue?', abort=True)
    for lDecoder,lTarget in lUpdatedDecoders:
      print (sh.cp('-av', lDecoder, lTarget))
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------
@dep.command()
@click.pass_context
def ipy( ctx ):
  '''Opens IPython to inspect the parser'''
  env = ctx.obj

  import IPython
  IPython.embed()
#------------------------------------------------------------------------------
