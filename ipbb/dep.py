from __future__ import print_function

# Modules
import click

#------------------------------------------------------------------------------
@click.group()
def dep():
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@dep.command()
@click.option('-o', '--output', default=None)
@click.pass_obj
def addrtab( env, output ):

  #------------------------------------------------------------------------------
  # Very messy, to be sorted out later
  from dep2g.Pathmaker import Pathmaker
  from dep2g.DepFileParser import DepFileParser

  lCfg = env.workConfig

  class dummy:pass
  lCommandLineArgs = dummy()
  lCommandLineArgs.define = ''
  lCommandLineArgs.product = lCfg['product']
  lCommandLineArgs.verbosity = 0


  lPathmaker = Pathmaker(env.src, 0)
  lDepFileParser = DepFileParser( lCommandLineArgs , lPathmaker )
  lDepFileParser.parse(lCfg['topPkg'], lCfg['topCmp'], lCfg['topDep'])

  from dep2g.AddressTableListMaker import AddressTableListMaker

  from dep_tree.SmartOpen import SmartOpen

  with SmartOpen( output ) as lTarget:
    AddressTableListMaker(lCommandLineArgs, lPathmaker).write(lTarget,lDepFileParser.ScriptVariables, lDepFileParser.Components, lDepFileParser.CommandList, None, None)

#------------------------------------------------------------------------------
