from __future__ import print_function

# Modules
import click

from dep_tree.SmartOpen import SmartOpen
from tools.common import makeParser

#------------------------------------------------------------------------------
@click.group()
def dep():
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def dump( env, output ):
  '''List source files'''
  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  with SmartOpen( output ) as lWriter:
    lWriter( str(lDepFileParser) )
#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
@dep.command()
@click.argument('group',type=click.Choice(['setup', 'src', 'addrtab', 'cgpfile']))
@click.option('-o', '--output', default=None)
@click.pass_obj
def cmds( env, group, output ):
  '''List source files'''
  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  with SmartOpen( output ) as lWriter:
    for addrtab in lDepFileParser.CommandList[group]:
      lWriter( addrtab.FilePath )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def addrtab( env, output ):
  '''List address table files'''

  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  from dep2g.AddressTableListMaker import AddressTableListMaker

  with SmartOpen( output ) as lWriter:
    for addrtab in lDepFileParser.CommandList["addrtab"]:
      lWriter( addrtab.FilePath )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def sources( env, output ):
  '''List source files'''

  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  with SmartOpen( output ) as lWriter:
    for addrtab in lDepFileParser.CommandList["src"]:
      lWriter( addrtab.FilePath )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def components( env, output ):

  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  with SmartOpen( output ) as lWriter:
    for lPkt, lCmps in lDepFileParser.Components.iteritems():
      lWriter('['+lPkt+']')
      for lCmp in lCmps:
        lWriter(lCmp)
      lWriter()

#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
def ipy( env ):
  '''Opens IPython to inspect the parser'''

  lDepFileParser, lPathmaker, lCommandLineArgs = makeParser(env)

  import IPython
  IPython.embed()
#------------------------------------------------------------------------------
