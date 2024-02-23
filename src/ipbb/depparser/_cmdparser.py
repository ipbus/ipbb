
import cerberus
import argparse
from ._cmdtypes import Command, IncludeCommand, SrcCommand, HlsSrcCommand, SetupCommand, AddrtabCommand
from ..console import cprint, console



cmds_defaults_schema = {
    "src": {
        'type': 'dict',
        'schema': {
            'vhdl2008': { 'type': 'boolean' },
            'vhdl2019': { 'type': 'boolean' },
            'lib': { 'type': 'string' },
        }
    }    
}

# -----------------------------------------------------------------------------
class ComponentAction(argparse.Action):
    '''
    Parses <module>:<component>
    '''
    def __init__(self, *args, **kwargs):
        self.append = kwargs.pop('append', False)
        super().__init__(*args, **kwargs)

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
        super().__init__(*args, **kwargs)
        self._choices = ['synth', 'sim']
        self.default = self._choices

    def __call__(self, parser, namespace, values, option_string=None):

        tokens = values.split(',')

        lInvalid = [t for t in tokens if t not in self._choices]
        if lInvalid:
            raise ValueError('Invalid source types '+','.join(lInvalid))

        setattr(namespace, self.dest, tokens )

# -----------------------------------------------------------------------------
class DepSubCmdParser(argparse.ArgumentParser):
    def error(self, message):
        raise DepCmdParserError(message)

# -----------------------------------------------------------------------------
class DepCmdParser(argparse.ArgumentParser):

    def error(self, message):
        raise DepCmdParserError(message)


    def validate_defaults(self):
        lValidator = cerberus.Validator(cmds_defaults_schema, allow_unknown=True)
        for pkg,defs in self.package_defaults.items():
            if not lValidator.validate(defs):
                cprint(f"ERROR: {pkg} repository settings validation failed", style='red')
                cprint(f"   Detected errors: {lValidator.errors}", style='red')
                cprint(f"   Settings: {defs}", style='red')
                raise RuntimeError(f"Package repo settings validation failed: {lValidator.errors}")

    # ---------------------------------
    def __init__(self, package_defaults : dict = {}):
        super().__init__(usage=argparse.SUPPRESS)

        self.package_defaults = package_defaults

        self.validate_defaults()

        # Common options
        lCompArgOpts = dict(action=ComponentAction, default=(None, None))

        parser_add = self.add_subparsers(dest='cmd', parser_class=DepSubCmdParser)

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
        vhdl_std_group = subp.add_mutually_exclusive_group()
        vhdl_std_group.add_argument('--vhdl2008', action='store_true', default=None)
        vhdl_std_group.add_argument('--vhdl2019', action='store_true', default=None)
        subp.add_argument('-u', '--usein', action=UseInAction)
        subp.add_argument('--simflags')
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


        self.creators = {
            'include' : lambda a : IncludeCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd),
            'src'     : lambda a : SrcCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.lib, a.vhdl2008, a.vhdl2019, 'synth' in a.usein, 'sim' in a.usein, a.simflags),
            'hlssrc'  : lambda a : HlsSrcCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.cflags, a.csimflags, a.tb, a.include_comp),
            'setup'   : lambda a : SetupCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.finalise),
            'addrtab' : lambda a  : AddrtabCommand(a.cmd, a.file, a.component[0], a.component[1], a.cd, a.toplevel),
            '*'       : lambda a  : Command(a.cmd, a.file, a.component[0], a.component[1], a.cd),
        }


    # --------------------------------------------------------------

    def parse_line(self, *args, current_package : str = None, current_component : str = None):

        # Parse commandline
        parsed_args = self.parse_args(*args)

        
        # Extract command identffier
        cmd = parsed_args.cmd if parsed_args.cmd in self.creators else '*'

        # Turn namespace into a dict
        vars_args = vars(parsed_args)

        # Apply current package and component
        p,c = vars_args["component"]
        if p is None and c is None:
            # case: -c not specified, current package and component
            p, c = current_package, current_component
        elif p is None and not c is None:
            # case: -c component
            p = current_package
        elif not p is None and c is None:
            # case: -c package:
            c = ""
        else:
            # Nothig to do
            pass
        vars_args["component"] = (p,c)

        # Get defaults for this package/command
        pkg_defs_args = self.package_defaults.get(p, {}).get(cmd, {})

        # Overlay defaults and parsed values
        dict_args = { k:(v if v is not None else pkg_defs_args.get(k)) for k,v in vars_args.items() } 

        # Go back to namespaces
        args = argparse.Namespace(**dict_args)

        # Create the Command object
        return self.creators[cmd](args)

# -----------------------------------------------------------------------------
# 