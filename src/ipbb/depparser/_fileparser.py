
import argparse
import os
import glob
import copy
import string
import re
import shlex
import cerberus

from ._definitions import dep_file_types, dep_command_types
from ._pathmaker import Pathmaker
from ._cmdparser import ComponentAction, DepCmdParser, DepCmdParserError
from ._cmdtypes import SrcCommand, IncludeCommand

from ..console import cprint, console
from ..tools.alien import AlienTree, AlienTemplate

from collections import OrderedDict
from os.path import exists, splitext, sep


repo_defaults_schema = {
    'vhdl_standard': { 'type': 'string', 'allowed': ['vhdl2008', 'vhdl1987'] },
    'default_library': { 'type': 'string' },
}

# -----------------------------------------------------------------------------
def _copy_update_command(aCmd, aFilePath, aPkg, aCmp):
    """
    Utility function to update parsed commands
    """
    cmd = copy.deepcopy(aCmd)
    cmd.filepath = aFilePath
    cmd.package = aPkg
    cmd.component = aCmp
    return cmd


# -----------------------------------------------------------------------------
class DepFile(object):
    """docstring for DepFile"""
    def __init__(self, aPackage, aComponent, aName, aPath, aParent):
        super().__init__()
        self.pkg = aPackage
        self.cmp = aComponent
        self.name = aName
        self.path = aPath
        self.parent = aParent
        self.entries = list()

        self.errors = list()
        self.unresolved = list()
        self.children = list()

    # -----------------------------------------------------------------------------
    def __str__(self):
        pathmaker = Pathmaker('', 1)
        return 'depfile {} | {}:{} - entries {}, errors {}, unresolved {}'.format(
            self.path, self.pkg, pathmaker.getPath('', self.cmp, 'include', self.name),
            len(self.entries), len(self.errors), len(self.unresolved)
        )

    # -----------------------------------------------------------------------------
    def itercmd(self):
        for en in self.entries:
            if isinstance(en, IncludeCommand):
                for rn in en.depfile.itercmd():
                    yield rn
            else:
                yield en

    # -----------------------------------------------------------------------------
    def iterchildren(self):
        yield self
        for f in self.children:
            for sf in f.iterchildren():
                yield sf



# -----------------------------------------------------------------------------
class InvalidDepDefaults(Exception):
    """Exception class for pre-parsing errors"""
    pass
# -----------------------------------------------------------------------------
#
# -----------------------------------------------------------------------------
class DepLineError(Exception):
    """Exception class for pre-parsing errors"""
    pass
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
class DepAssignmentError(Exception):
    """Exception class for pre-parsing errors"""
    pass
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
class State(object):
    """Utility class that holds the current status of the parser
    while iterating through the tree of dependencies"""
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.currentfile = None

    @property
    def tab(self):
        return ' ' * 4 * self.depth
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class DepFileParser(object):
    """
    Dependency file parser class
    """
    # -----------------------------------------------------------------------------
    @staticmethod
    def forward_parsing(aDepFileName):

        ftype = dep_file_types.get(splitext(aDepFileName)[1], None)
        if ftype is not None:
            return ftype['fwd']
        return True

    @property
    def rootdir(self):
        return self._pathMaker._rootdir

    @staticmethod
    def repo_settings_to_defaults(repo_settings):

        vtor = cerberus.Validator(repo_defaults_schema)
        errors = {}

        pkg_defaults = {}
        for pkg,settings in repo_settings.items():

            if not vtor.validate(settings):
                errors[pkg] = vtor.errors

            src_cmd = {}
            if 'vhdl_standard' in settings:
                src_cmd['vhdl2008'] = settings['vhdl_standard'] == 'vhdl2008'
            if 'default_library' in settings:
                src_cmd['lib'] = settings['default_library']
            pkg_defaults[pkg] = {'src': src_cmd }


        if errors:
            cprint(f"ERROR: Repository settings validation failed", style='red')
            cprint(f"   Detected errors: {errors}", style='red')
            cprint(f"   Settings: {repo_settings}", style='red')
            raise InvalidDepDefaults(f"Project settings validation failed: {errors}")


        return pkg_defaults



    # -----------------------------------------------------------------------------
    def __init__(self, aToolSet, aPathmaker, aRepoSettings={}, aVerbosity=0):
        # --------------------------------------------------------------
        # Member variables
        self._toolset = aToolSet
        self._verbosity = aVerbosity
        # helper object to resolve files in the work area
        self._pathMaker = aPathmaker
        # Helper object holding the parser state while traversing the dependency tree 
        self._state = None
        # list of all known depfiles
        self._depregistry = OrderedDict()

        # Results
        self.depfile = None
        self.settings = AlienTree()
        self.libs = set()
        self.packages = OrderedDict()

        self.commands = {c: [] for c in dep_command_types}

        self.unresolved = list()
        self.errors = list()

        # --------------------------------------------------------------
        self.pkg_defaults = self.repo_settings_to_defaults(aRepoSettings)

        # --------------------------------------------------------------
        # Set the toolset
        self.settings['toolset'] = self._toolset

        # --------------------------------------------------------------
        # Set up the parser
        self.cmdparser = DepCmdParser(self.pkg_defaults)

    # -----------------------------------------------------------------------------

    # -----------------------------------------------------------------------------
    @property
    def unresolved_paths(self):
        lNotFound = set()

        for lPathExpr, aCmd, lPackage, lComponent, lDepFilePath, lDepPackage, lDepComponent in self.unresolved:
            lNotFound.add(lPathExpr)

        return lNotFound
    # -----------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    @property
    def unresolved_packages(self):
        lNotFound = set()

        for lPathExpr, lCmd, lPackage, lComponent, lDepPackage, lDepComponent, lDepFilePath in self.unresolved:
            if os.path.exists(self._pathMaker.getPath(lPackage)):
                continue

            lNotFound.add(lPackage)
        return lNotFound

    # -------------------------------------------------------------------------
    @property
    def unresolved_components(self):
        lNotFound = OrderedDict()

        for lPathExpr, lCmd, lPackage, lComponent, lDepPackage, lDepComponent, lDepFilePath in self.unresolved:
            if os.path.exists(self._pathMaker.getPath(lPackage, lComponent)):
                continue

            lNotFound.setdefault(lPackage, set()).add(lComponent)

        return lNotFound

    # -----------------------------------------------------------------------------
    @property
    def unresolved_files(self):
        lNotFound = OrderedDict()
        for lPathExpr, lCmd, lPackage, lComponent, lDepPackage, lDepComponent, lDepFilePath in self.unresolved:
            lNotFound.setdefault(
                lPackage,
                OrderedDict()
            ).setdefault(
                lComponent,
                OrderedDict()
            ).setdefault(
                lPathExpr,
                set()
            ).add(lDepFilePath)

        return lNotFound

    # -------------------------------------------------------------------------
    def _line_drop_Comments(self, aLine):
        '''Drop blank lines and comments
        '''
        lLine = aLine.strip()

        # Ignore blank lines and comments
        if lLine != "" and lLine[0] != "#":
            # Return None (i.e. continue)
            return lLine

        # Return None (i.e. continue)
        return

    # -------------------------------------------------------------------------
    def _line_process_assignments(self, aLine: str):
        # Process the assignment directive
        
        pattern = re.compile(r'^([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)*)?\s*=\s*(.*)$')
        # group 1: settings name
        # group 2: invalid setting name
        # group 3: rest of the line
        pattern = re.compile(r'^(?:([a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)*)|([^=\n\s]*))\s*=\s*(.*)?$')

        if aLine[0] != "@":
            return aLine

        lLine = aLine[1:].strip()

        # Validate assignment structure
        m = pattern.match(aLine[1:].strip())

        if m is None:
            raise DepAssignmentError(f"Assignment expression does not have the key = value form '{lLine}'")
        elif not m.group(2) is None:
            raise DepAssignmentError(f"Invalid variable name {m.group(2)}")
        elif not m.group(3):
            raise DepAssignmentError(f"Missing assignment value '(lLine'")

        lPar, lExpr = m.group(1), m.group(3)

        # Validate expression
        

        if lPar in self.settings:
            console.log(f"WARNING: '{lPar.strip()}' is already defined with value '{self.settings[lPar.strip()]}'. New value will not be applied ({lExpr}).", style='yellow')
        else:
            lOldLock = self.settings.locked
            self.settings.lock(True)
            try:
                # exec(aLine[1:], None, self.settings)
                x = eval(lExpr, None, self.settings)
            except Exception as lExc:
                cprint(lExc)
                raise DepLineError("VariableAssignmentError") from lExc
            self.settings.lock(lOldLock)
            self.settings[lPar] = x

        if self._verbosity > 1:
            print(self._state.tab, ':', aLine)

        # Return None (i.e. continue)
        return

    # -------------------------------------------------------------------------
    def _line_process_conditional(self, aLine):
        if aLine[0] != "?":
            return aLine

        lTokens = [i for i, letter in enumerate(
            aLine) if letter == "?"]
        if len(lTokens) != 2:
            raise DepLineError(
                "There must be precisely two '?' tokens per line. Found {0}'".format(len(lTokens))
            )

        try:
            lExprValue = eval(
                aLine[lTokens[0] + 1: lTokens[1]], None, self.settings
            )
        except Exception as lExc:
            raise DepLineError("Parsing directive failed") from lExc

        if not isinstance(lExprValue, bool):
            raise DepLineError("Directive does not evaluate to boolean type in {0}".format(lExprValue))

        # Expression evaluated false
        if not lExprValue:
            return

        # if line is accepted, strip the conditionality from the
        # front and carry on
        aLine = aLine[lTokens[1] + 1:].strip()

        return aLine

    # -------------------------------------------------------------------------
    def _line_replace_vars(self, aLine):
        try:
            lLine = AlienTemplate(aLine).substitute(self.settings)
        except RuntimeError as lExc:
            raise DepLineError("Template substitution failed") from lExc

        return lLine

# -------------------------------------------------------------------------
    def _resolve_paths(self, aParsedCmd, aCurComponent, aParentDep):

        # --------------------------------------------------------------
        lPackage = aParsedCmd.package
        lComponent = aParsedCmd.component
        # --------------------------------------------------------------
        # Set the target file expression, whether specified explicitly
        # or not
        if (not aParsedCmd.filepath):
            lComponentName = lComponent.split(sep)[-1]

            f, u = self._pathMaker.globall(
                lPackage, lComponent, aParsedCmd.cmd, 
                self._pathMaker.getDefNames(aParsedCmd.cmd, lComponentName),
                cd=aParsedCmd.cd
            )

            if len(f) == 1:
                lFileLists, lUnmatchedExprs = f, []
            else:
                # FIXME! This is confusing!
                # It mixes the not match and multiple matches case!
                lFileLists = []
                lUnmatchedExprs = [self._pathMaker.getPath(
                    lPackage, lComponent, aParsedCmd.cmd, 
                    self._pathMaker.getDefNames(aParsedCmd.cmd, lComponentName, 'braces'),
                    cd=aParsedCmd.cd
                    )
                ]
        else:
            lFileLists, lUnmatchedExprs = self._pathMaker.globall(
                lPackage, lComponent, aParsedCmd.cmd, 
                aParsedCmd.filepath,
                cd=aParsedCmd.cd
            )

        lEntries = list()

        # --------------------------------------------------------------
        # Create the entries
        for lFileList in lFileLists:
            for lFile, lFilePath in lFileList:
                # --------------------------------------------------------------
                # Debugging
                if self._verbosity > 0:
                    print(self._state.tab, ' ',
                          aParsedCmd.cmd, lFile, lFilePath)
                # --------------------------------------------------------------
                cmd = _copy_update_command(aParsedCmd, lFilePath, lPackage, lComponent)
                # If an include command, parse the sub-dep files
                if aParsedCmd.cmd == "include":
                    cmd.depfile = self._parse_file(lPackage, lComponent, lFile, aParentDep)
                lEntries.append(cmd)


        return lEntries, (lUnmatchedExprs, lPackage, lComponent)
        # --------------------------------------------------------------

    # -------------------------------------------------------------------------
    def _parse_file(self, aPackage, aComponent, aDepFileName, aParentDep):
        """
        Private method implementing depfile parsing
        Used for recursion

        Parsing includes
        - Reading the dep file
        - Pre-process input
        - Parse commands
        - Store commands in a depfile object
        """
        lDepFilePath = self._pathMaker.getPath(
            aPackage, aComponent, 'include', aDepFileName)

        if lDepFilePath in self._depregistry:
            return self._depregistry[lDepFilePath]

        if self._verbosity > 1:
            print('>' * self._state.depth, 'Parsing',
                  aPackage, aComponent, aDepFileName)

        # This shouldn't be needed, case already covered elsewhere
        if not exists(lDepFilePath):
            self.unresolved.append(
                (lDepFilePath, 'include', aPackage, aComponent, '__top__', '__top__', '__top__'))
            raise OSError("File " + lDepFilePath + " does not exist")

        # Ok, this is a new file. Let's dig in
        self._state.depth += 1

        lCurrentFile = DepFile(aPackage, aComponent, aDepFileName, lDepFilePath, aParentDep)
        self._depregistry[lDepFilePath] = lCurrentFile

        with open(lDepFilePath) as lDepFile:
            for lLineNr, lLine in enumerate(lDepFile):

                # --------------------------------------------------------------
                # Pre-processing
                try:
                    # Sanitize/drop comments
                    lLine = self._line_drop_Comments(lLine)
                    if not lLine:
                        continue

                    # Process variable assignment directives
                    lLine = self._line_process_assignments(lLine)
                    if not lLine:
                        continue

                    # Process conditional directives
                    lLine = self._line_process_conditional(lLine)
                    if not lLine:
                        continue

                    # Replace variables
                    lLine = self._line_replace_vars(lLine)

                except DepLineError as lExc:
                    lCurrentFile.errors.append((aPackage, aComponent, aDepFileName, lDepFilePath, lLineNr, lLine, lExc))
                    continue

                # --------------------------------------------------------------
                # Parse the line using arg_parse
                try:
                    lParsedCmd = self.cmdparser.parse_line(shlex.split(lLine), current_package=aPackage, current_component=aComponent)
                except DepCmdParserError as lExc:
                    lCurrentFile.errors.append((aPackage, aComponent, aDepFileName, lDepFilePath, lLineNr, lLine, lExc))
                    continue

                if self._verbosity > 1:
                    print(self._state.tab, '- Parsed line', vars(lParsedCmd))

                # --------------------------------------------------------------
                lEntries, (lUnresolvedExpr, lParsedPackage, lParsedComponent) = self._resolve_paths(lParsedCmd, lDepFilePath, lCurrentFile)
                lCurrentFile.entries += lEntries
                if lParsedCmd.cmd == 'include':
                    for inc in lEntries:
                        lCurrentFile.children.append(inc.depfile)

                # Log unresolved entries
                lCurrentFile.unresolved += [
                    (lExpr, lParsedCmd.cmd, lParsedPackage, lParsedComponent, aPackage, aComponent, lDepFilePath)
                    for lExpr in lUnresolvedExpr
                ]

                if self._verbosity > 1:
                    print(self._state.tab, '  -- Entries of', aDepFileName, ':', lEntries)

        if not self.forward_parsing(aDepFileName):
            lCurrentFile.entries.reverse()

        if self._verbosity > 1:
            print(self._state.tab, lCurrentFile)

            print('<' * self._state.depth)
        self._state.depth -= 1

        # TODO
        # Add me to the file registry
        return lCurrentFile

    # -------------------------------------------------------------------------
    def _gather_summary_info(self):
        """
        Gather DepTree summart information"
        """
        for lCmd in self.depfile.itercmd():
            if self._verbosity > 0:
                print (lCmd)
            self.commands[lCmd.cmd].append(lCmd)
            self.packages.setdefault(
                lCmd.package, []).append(lCmd.component)
            if isinstance(lCmd, SrcCommand) and lCmd.lib is not None:
                self.libs.add(lCmd.lib)

    # -------------------------------------------------------------------------
    def _gather_unresolved_and_errors(self):
        """
        Gather unresolved files and errors
        """

        for dp, f in self._depregistry.items():
            self.errors.extend(f.errors)
            self.unresolved.extend(f.unresolved)

    # -------------------------------------------------------------------------
    def _remove_duplicates(self):
        """
        Remove duplicates from command and package list
        """

        self.commands = { k:list(OrderedDict.fromkeys(v)) for k,v in self.commands.items() }

        # If we are exiting the top-level, uniquify the component list
        for p in self.packages:
            self.packages[p] = list(OrderedDict.fromkeys(self.packages[p])) 


    # -------------------------------------------------------------------------
    def _apply_defaults(self):

        from functools import reduce
        def deep_get(dictionary, keys, default=None):
            return reduce(lambda d, key: d.get(key, default) if isinstance(d, dict) else default, keys.split("."), dictionary)

        pkg_lib_map = self.settings.get('pkg2lib_map', None)

        for k,cmds in self.commands.items():
            for c in cmds:
                if isinstance(c, SrcCommand) and c.lib is None and not pkg_lib_map is None:
                        c.lib = pkg_lib_map.get(c.package, None)

  
    # -------------------------------------------------------------------------
    def parse(self, aPackage, aComponent, aDepFileName):

        # TODO: create a reset method
        self._state = State()

        # Do the parsing here
        self.depfile = self._parse_file(aPackage, aComponent, aDepFileName, None)

        # Lock the config variables tree
        self.settings.lock(True)
        # --------------------------------------------------------------
        # If we are exiting the top-level, uniquify the commands list, keeping
        # the order as defined in Dave's origianl voodoo
        if self._state.depth != 0:
            raise RuntimeError(f"Something went wrong while parsing {aPackage}:{aComponent} {aDepFileName}")
        self._state = None


        # Post parsing
        self._gather_summary_info()

        self._gather_unresolved_and_errors()

        # Uniquify
        self._remove_duplicates()

        # Apply default settings
        self._apply_defaults()



        # --------------------------------------------------------------

    # -------------------------------------------------------------------------
