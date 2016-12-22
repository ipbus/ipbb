import argparse

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class CommandLineParser(object):
  #--------------------------------------------------------------
  def __init__(self):
    defaultString=' (default: \'%(default)s\')'
    parser = argparse.ArgumentParser(description = 'Parse design dependency tree and generate build scripts and other useful files '+defaultString, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument( '-v' , '--verbosity' , action = 'count' , help = 'verbosity'+defaultString)
    parser.add_argument( '-m' , '--componentmap' , type = file , metavar = 'component_map' , help = 'location of component map file'+defaultString)
    parser.add_argument( '-D' , '--define' , metavar = 'key=value' , default=[] , help='Define or override script variables'+defaultString , action='append')
    parser.add_argument( '-o' , '--output' , metavar = 'file' , help = 'output file (outputs to stdout if unspecified)'+defaultString )
    parser.add_argument( 'toolset' , metavar = 'toolset' , help = 'output product: xtclsh (xtclsh script); vivado (vivado script); sim (Modelsim script); components (component list}; addrtab (address table list); b (address decoder script); files (flat file list)'+defaultString)
    parser.add_argument( 'rootdir' , metavar = 'sandbox_root' , help = 'Sandbox root'+defaultString)
    parser.add_argument( 'topdir' , metavar = 'top_dir' , help = 'top level design directory'+defaultString)
    parser.add_argument( 'depfile' , nargs = '?' , metavar = 'top_depfile' , default = 'top.dep', help = 'top level dep file'+defaultString )
    self.parse = parser.parse_args
  #--------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
