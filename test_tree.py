#!/bin/env python


from dep_tree.DepFileParser import DepFileParser
from dep_tree.Pathmaker import Pathmaker

class dummy:
  pass

lCommandLineArgs = dummy()

# lCommandLineArgs.rootdir = '/net/home/ppd/thea/Development/ipbus/test/cactusupgrades/ipbus-fw-test'
# lCommandLineArgs.topdir = 'boards/kc705/base_fw/kc705_gmii/synth/'
lCommandLineArgs.rootdir = '/net/home/ppd/thea/Development/ipbus/test/cactusupgrades'
lCommandLineArgs.topdir = 'my-proj:projects/example/'
lCommandLineArgs.depfile = 'top_kc705_gmii.dep'
lCommandLineArgs.define = []
lCommandLineArgs.product = 'vivado'
lCommandLineArgs.componentmap = None
lCommandLineArgs.verbosity = 1

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

import IPython
IPython.embed()
