
import argparse
from ._cmdtypes import Command, IncludeCommand, SrcCommand, HlsSrcCommand, SetupCommand, AddrtabCommand

# -----------------------------------------------------------------------------
class ComponentAction(argparse.Action):
    '''
    Parses <module>:<component>
    '''
    def __init__(self, *args, **kwargs):
        self.append = kwargs.pop('append', False)
        super(ComponentAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):

        lSeparators = values.count(':')
        # Validate the format
        if lSeparators > 1:
            raise argparse.ArgumentTypeError(
                'Malformed component name : %s. Expected <module>:<component>' % values)

        lTokenized = values.split(':')
        if len(lTokenized) == 1:
            lTokenized.insert(0, None)
        result = tuple(lTokenized)

        if not self.append:
            setattr(namespace, self.dest, result)
        else:
            if not getattr(namespace, self.dest):
                setattr(namespace, self.dest, [])

            getattr(namespace, self.dest).append(result)


# -----------------------------------------------------------------------------
class DepCmdParserError(Exception):
    pass

# -----------------------------------------------------------------------------
class UseInAction(argparse.Action):
    def __init__(self, *args, **kwargs):
        super(UseInAction, self).__init__(*args, **kwargs)
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
        subp.add_argument('--vhdl2008', action='store_true')
        subp.add_argument('-u', '--usein', action=UseInAction)
        subp.add_argument('file', nargs='+')

        # Source sub-parser
        subp = parser_add.add_parser('hlssrc')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('--tb', action='store_true')
        subp.add_argument('--cflags')
        subp.add_argument('--csimflags')
        subp.add_argument('-i', '--include-comp', append=True, action=ComponentAction, default=[])
        subp.add_argument('file', nargs='+')

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
            'include' : lambda a : IncludeCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd),
            'src'     : lambda a : SrcCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.lib, a.vhdl2008, 'synth' in a.usein, 'sim' in a.usein),
            'hlssrc'  : lambda a : HlsSrcCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.cflags, a.csimflags, a.tb, a.include_comp),
            'setup'   : lambda a : SetupCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.finalise),
            'addrtab' : lambda a : AddrtabCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.toplevel),
            '*'       : lambda a : Command(a.cmd, a.file, a.component[0], a.component[1], a.cd),
        }


    # --------------------------------------------------------------

    def parseLine(self, *args, **kwargs):

        args = self.parse_args(*args, **kwargs)

        cmd = args.cmd if args.cmd in self.callbacks else '*'
        return self.callbacks[cmd](args)

# -----------------------------------------------------------------------------

