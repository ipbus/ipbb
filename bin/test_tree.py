#!/bin/env python
import argparse

parser = argparse.ArgumentParser(usage = argparse.SUPPRESS)
parser.add_argument('-b', dest='interactive', default=True, action='store_false')
parser_add = parser.add_subparsers(dest = "cmd")
parser.add_argument('--verbose', '-v', action='count')
subp = parser_add.add_parser('legacy')
subp = parser_add.add_parser('dev')
subp.add_argument('-p','--printparser', default=False, action='store_true')
subp.add_argument('-c','--create', default=False, action='store_true')
subp = parser_add.add_parser('mp7')
subp.add_argument('-p','--printparser', default=False, action='store_true')
subp.add_argument('-c','--create', default=False, action='store_true')

args = parser.parse_args()

print args
print args.cmd
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
lCommandLineArgs.verbosity = args.verbose

if args.cmd == 'legacy':
    from dep_tree.DepFileParser import DepFileParser
    from dep_tree.Pathmaker import Pathmaker

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

    # 
elif args.cmd in ['dev','mp7']:

    lCommandLineArgs.rootdir = '/home/ale/Development/ipbus-upgr/test_envs/xyz/src'

    from dep2g.Pathmaker import Pathmaker as Pathmaker2g
    from dep2g.DepFileParser import DepFileParser as DepFileParser2g

    lPathmaker = Pathmaker2g( lCommandLineArgs.rootdir, lCommandLineArgs.verbosity )
    lDepFileParser = DepFileParser2g( lCommandLineArgs , lPathmaker )

    if args.cmd == 'dev':
        lDepFileParser.parse( 'dummy-fw-proj', 'projects/example', 'top_kc705_gmii.dep')
    elif args.cmd == 'mp7':
        lDepFileParser.parse( 'cactusupgrades', 'projects/examples/mp7xe_690', 'top.dep')

    if args.printparser:
        print lDepFileParser
    
    if args.create:
        from dep2g.VivadoProjectMaker import VivadoProjectMaker
        import tools.xilinx

        lDummy = dummy()
        lDummy.output = ''
        lWriter = VivadoProjectMaker(lDummy, lPathmaker)
        lTarget = tools.xilinx.VivadoConsole()
        lWriter.write(lTarget,lDepFileParser.ScriptVariables, lDepFileParser.Components, lDepFileParser.CommandList, None, None)


if args.interactive:
    import IPython
    IPython.embed()
