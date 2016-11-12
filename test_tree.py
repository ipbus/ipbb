#!/bin/env python
import argparse

from dep_tree.DepFileParser import DepFileParser
from dep_tree.Pathmaker import Pathmaker


parser = argparse.ArgumentParser(usage = argparse.SUPPRESS)
parser.add_argument('-b', dest='interactive', default=True, action='store_false')
parser.add_argument('-l', dest='legacy', default=False, action='store_true')
args = parser.parse_args()

class dummy:
  pass

lCommandLineArgs = dummy()

# lCommandLineArgs.rootdir = '/net/home/ppd/thea/Development/ipbus/test/cactusupgrades/ipbus-fw-test'
# lCommandLineArgs.topdir = 'boards/kc705/base_fw/kc705_gmii/synth/'
lCommandLineArgs.rootdir = '/net/home/ppd/thea/Development/ipbus/test/cactusupgrades'
lCommandLineArgs.topdir = 'dummy-fw-proj:projects/example/'
lCommandLineArgs.depfile = 'top_kc705_gmii.dep'
lCommandLineArgs.define = []
lCommandLineArgs.product = 'vivado'
lCommandLineArgs.componentmap = None
lCommandLineArgs.verbosity = 2

if args.legacy:
    # lPathmaker = Pathmaker( lCommandLineArgs.rootdir , lCommandLineArgs.topdir , lCommandLineArgs.componentmap , lCommandLineArgs.verbosity )
    lPathmaker = Pathmaker( lCommandLineArgs.rootdir, lCommandLineArgs.componentmap , lCommandLineArgs.verbosity )
    lDepFileParser = DepFileParser( lCommandLineArgs , lPathmaker )

    #--------------------------------------------------------------
    # Set the entrypoint for depfile parsing
    lTopFile = lPathmaker.getpath( lCommandLineArgs.topdir , "include" , lCommandLineArgs.depfile )
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Parse the requested dep file
    lDepFileParser.parse( lTopFile , lCommandLineArgs.topdir )
    #--------------------------------------------------------------
else:

    lCommandLineArgs.rootdir = '/home/ale/Development/ipbus-upgr/integration/sandbox'

    from dep_tree.Pathmaker2g import Pathmaker as Pathmaker2g
    from dep_tree.DepFileParser2g import DepFileParser as DepFileParser2g

    lPathmaker = Pathmaker2g( lCommandLineArgs.rootdir, lCommandLineArgs.verbosity )
    lDepFileParser = DepFileParser2g( lCommandLineArgs , lPathmaker )

    lDepFileParser.parse( 'dummy-fw-proj', 'projects/example', 'top_kc705_gmii.dep')

    print '\n'.join([str(id) for id in lDepFileParser.ComponentIds])

    from dep_tree.VivadoScriptWriter import VivadoScriptWriter

    lDummy = dummy()
    lDummy.output = 'here.tcl'
    lWriter = VivadoScriptWriter(lDummy, lPathmaker)
    lWriter.write(lDepFileParser.ScriptVariables, lDepFileParser.ComponentIds, lDepFileParser.CommandList, None, None)

    lLines = [ l.strip() for l in open('here.tcl').readlines() ]
    import xilinx.vivado

if args.interactive:
    import IPython
    IPython.embed()
