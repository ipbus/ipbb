from __future__ import print_function, absolute_import

import argparse
from ._cmdtypes import FileCommand, IncludeCommand, SrcCommand, SetupCommand, AddrtabCommand

# -----------------------------------------------------------------------------
class ComponentAction(argparse.Action):
    '''
    Parses <module>:<component>
    '''

    def __call__(self, parser, namespace, values, option_string=None):
        lSeparators = values.count(':')
        # Validate the format
        if lSeparators > 1:
            raise argparse.ArgumentTypeError(
                'Malformed component name : %s. Expected <module>:<component>' % values)

        lTokenized = values.split(':')
        if len(lTokenized) == 1:
            lTokenized.insert(0, None)

        setattr(namespace, self.dest, tuple(lTokenized))


# -----------------------------------------------------------------------------
class DepCmdParserError(Exception):
    pass

# -----------------------------------------------------------------------------
class SrcTypeAction(argparse.Action):
    def __init__(self, *args, **kwargs):
        super(SrcTypeAction, self).__init__(*args, **kwargs)
        self._choices = ['synth', 'sim']
        self.default = self._choices

    def __call__(self, parser, namespace, values, option_string=None):

        tokens = values.split(',')
        
        lInvalid = [t for t in tokens if t not in self._choices]
        if lInvalid:
            raise ValueError('Invalid source types '+','.join(lInvalid))

        setattr(namespace, self.dest, tokens )


# -----------------------------------------------------------------------------
class DepCmdParser(argparse.ArgumentParser):
    def error(self, message):
        raise DepCmdParserError(message)

    # ---------------------------------
    def __init__(self, *args, **kwargs):
        super(DepCmdParser, self).__init__(*args, **kwargs)

        # Common options
        lCompArgOpts = dict(action=ComponentAction, default=(None, None))

        parser_add = self.add_subparsers(dest='cmd', parser_class=argparse.ArgumentParser)

        # Include sub-parser
        subp = parser_add.add_parser('include')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='*')

        # Setup sub-parser
        subp = parser_add.add_parser('setup')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='*')
        subp.add_argument('-f', '--finalise', action='store_true')

        # Utilites sub-parser
        subp = parser_add.add_parser('util')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='*')

        # Source sub-parser
        subp = parser_add.add_parser('src')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('-l', '--lib')
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='+')
        subp.add_argument('--vhdl2008', action='store_true')
        subp.add_argument('-t', '--tyoe', action=SrcTypeAction)

        # Address table sub-parser
        subp = parser_add.add_parser('addrtab')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('-t', '--toplevel', action='store_true')
        subp.add_argument('file', nargs='*')

        # Ip repository sub-parser
        subp = parser_add.add_parser('iprepo')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='*')


        self.callbacks = {
            'include' : lambda a : IncludeCommand(a.cmd, a.file, None, None),
            'src'     : lambda a : SrcCommand(a.cmd, a.file, None, None, a.vhdl2008),
            'setup'   : lambda a : SetupCommand(a.cmd, a.file, None, None, a.finalise),
            'addrtab'  : lambda a : AddrtabCommand(a.cmd, a.file, None, None, a.toplevel),
            '*'       : lambda a : FileCommand(a.cmd, a.file, None, None),
        }


    # --------------------------------------------------------------

    def parseLine(self, *args, **kwargs):

        return self.parse_args(*args, **kwargs)
        # args = self.parse_args(*args, **kwargs)

        # cmd = args.cmd if args.cmd in self.callbacks else '*'

        # return self.callbacks[cmd](args)

# -----------------------------------------------------------------------------

