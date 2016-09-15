import argparse

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class CommandLineParser(object):
  #--------------------------------------------------------------
  def __init__(self):
    parser = argparse.ArgumentParser(description = "Parse design dependency tree and generate build scripts and other useful files")
    parser.add_argument( "-v" , "--verbosity" , action = "count" , help = "verbosity")
    parser.add_argument( "-p" , "--product" , metavar = "product" , help = "output product: x (xtclsh script); v (vivado script); s (Modelsim script); c (component list}; a (address table list); b (address decoder script); f (flat file list)")
    parser.add_argument( "-m" , "--componentmap" , type = file , metavar = "component_map" , help = "location of component map file")
    parser.add_argument( "-D" , "--define" , metavar = "key=value" , default=[] , help='Define or override script variables' , action='append')
    parser.add_argument( "-o" , "--output" , metavar = "file" , help = "output file (outputs to stdout if unspecified)" )    
    parser.add_argument( "root" , metavar = "repos_root" , help = "repository root")
    parser.add_argument( "top" , metavar = "top_dir" , help = "top level design directory")
    parser.add_argument( "dep" , nargs = "?" , metavar = "top_depfile" , help = "top level dep file" , default = "top.dep")
    self.parse = parser.parse_args
  #--------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
