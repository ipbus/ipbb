#!/bin/env python

'''
Usage:

dep_tree.py [-h] [-v] [-p P] [-m component_map]
           repos_root top_dir [top_depfile]

Parse design dependency tree and generate build scripts and other useful files

positional arguments:
  repos_root    repository root
  top_dir       top level design directory
  top_depfile     top level dep file

optional arguments:
  -h, --help    show this help message and exit
  -v        verbosity
  -p P        output product: x (xtclsh script); s (Modelsim script); c
          (component list}; a (address table list); b (address
          decoder script); f (flat file list)
  -m component_map  location of component map file
  -D set or override script directives

  default: nothing is done

---

Repository layout in each component / top-level area:

firmware/cfg: contains .dep files and project config files
firmware/hdl: contains source files
firmware/cgn: contains XCO core build files
/addr_table: contains uHAL address table XML files

---

.dep file format

# Comment line

common options:

  -c component_name: look under different component to find referenced file
  -d: descend a level in dir tree to find referenced file
  -s dir: look in subdir path to find referenced file

include [dep_file_list]

  default is to take file component_name.dep

setup [-z] [tcl_file_list]

  default is to take file component_name.tcl
  -z: coregen project configuration script

src [-l library] [-g] [-n] src_file_list

  src_file_list under firmware/hdl by default; may contain glob patterns
  -g: find 'generated' src in ipcore directory
  -n: for XCO files, build but don't include

addrtab [-t] [file_list]

  default is to reference file component_name.xml
  -t: top-level address table file

---

component_map file format

logical_name physical_dir

  The 'physical_dir' is relative to the trunk/

'''

from __future__ import print_function
import argparse
import sys
import os
import time
import glob

from dep_tree.DepFileParser import DepFileParser
from dep_tree.CommandLineParser import CommandLineParser
from dep_tree.Pathmaker import Pathmaker


from dep_tree.AddressTableGeneratorWriter import AddressTableGeneratorWriter
from dep_tree.AddressTableListWriter import AddressTableListWriter
from dep_tree.ComponentListWriter import ComponentListWriter
from dep_tree.IPCoreSimScriptWriter import IPCoreSimScriptWriter
from dep_tree.ModelsimScriptWriter import ModelsimScriptWriter
from dep_tree.SourceListWriter import SourceListWriter
from dep_tree.SourceListWriter2 import SourceListWriter2
from dep_tree.XtclshScriptWriter import XtclshScriptWriter
from dep_tree.VivadoScriptWriter import VivadoScriptWriter


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def main():

  #--------------------------------------------------------------
  # Set up the three objects which do the real hardwork
  lCommandLineArgs = CommandLineParser().parse()
  lPathmaker = Pathmaker( lCommandLineArgs.root , lCommandLineArgs.top , lCommandLineArgs.componentmap , lCommandLineArgs.verbosity )
  lDepFileParser = DepFileParser( lCommandLineArgs , lPathmaker )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  # Assign the product handlers to the appropriate commandline flag and check we know how to handle the requested product
  lWriters = {
                "component":ComponentListWriter , # Output file lists
                "files":SourceListWriter ,        # Output file lists
                "files2":SourceListWriter2 ,      # Output file lists
                "addrtab":AddressTableListWriter ,# Output file lists
                "b":AddressTableGeneratorWriter , # Output address table generator file
                "sim":ModelsimScriptWriter ,      # Output Modelsim script
                "ip":IPCoreSimScriptWriter ,      # Output IPSim script
                "xtclsh":XtclshScriptWriter  ,    # Output xtclsh script
                "vivado":VivadoScriptWriter       # Output vivado script
              }

  if lCommandLineArgs.product not in lWriters:
    raise SystemExit( "No handler for product option '{0}' supplied".format( lCommandLineArgs.product ) )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  # Set the entrypoint for depfile parsing
  lTopFile = lPathmaker.getpath( lCommandLineArgs.top , "include" , lCommandLineArgs.dep )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  # Debugging
  if lCommandLineArgs.verbosity > 0:
    print( "Top:" , lTopFile )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  # Parse the requested dep file
  lDepFileParser.parse( lTopFile , lCommandLineArgs.top )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  # Debugging
  if lCommandLineArgs.verbosity > 0:
    print( "-"*20 )
    for i,j in sorted( lDepFileParser.CommandList.iteritems() ):
      print( i , ":" , len( j ) , "files" )
    print( "-"*20 )
    print( "Build settings:" )
    for i,j in sorted( lDepFileParser.ScriptVariables.iteritems() ):
      print( "  " , i , ":" , j )
    print( "-"*20 )

  if len( lDepFileParser.FilesNotFound ):
    print( "-"*20 )
    print( "Warning: Files not found" )
    for i in lDepFileParser.FilesNotFound:
      print ( ">" , i )
    print( "-"*20 )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  # Look up the Writer object in the dictionary, create an object of that type and call the write function
  try:
      lWriters[lCommandLineArgs.product]( lCommandLineArgs , lPathmaker ).write( lDepFileParser.ScriptVariables , lDepFileParser.ComponentPaths , lDepFileParser.CommandList , lDepFileParser.Libs, lDepFileParser.Maps )
  except Exception as e:
      import sys, traceback
      traceback.print_exc(file=sys.stdout)
      print('ERROR:', e)
      raise SystemExit(-1)
  #--------------------------------------------------------------

  raise SystemExit(0)
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    main()
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
