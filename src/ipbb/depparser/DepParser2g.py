from __future__ import print_function, absolute_import
from future.utils import raise_from
from future.utils import iterkeys, itervalues, iteritems

import argparse
import os
import glob
from . import Pathmaker
from ..tools.common import DictObj
from collections import OrderedDict
from os.path import exists, splitext
from string import Template


# -----------------------------------------------------------------------------
class Command(object):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd       (str): command directive
        FilePath  (str): absolute, normalised path to the command target.
        Package   (str): package the target belongs to.
        Component (str): component withon 'Package' the target belongs to
    """

    def __init__(self, aCmd, aFilePath, aPackage, aComponent):
        super(Command, self).__init__()
        self.cmd = aCmd
        self.FilePath = aFilePath
        self.Package = aPackage
        self.Component = aComponent

    def __str__(self):
        return '{ \'{}\', component: \'{}:{}\' }' % (
            self.cmd, self.FilePath, self.Package, self.Component
        )


# -----------------------------------------------------------------------------
class FileCommand(Command):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd       (str):  command directive
        FilePath  (str):  absolute, normalised path to the command target.
        Package   (str):  package the target belongs to.
        Component (str):  component withon 'Package' the target belongs to
        Lib       (str):  library the file will be added to
        Include   (bool): src-only flag, used to include/exclude target from projects
        TopLevel  (bool): addrtab-only flag, identifies address table as top-level
        Vhdl2008  (bool): src-only flag, toggles the vhdl 2008 syntax for .vhd files
        Finalise  (bool): setup-only flag, identifies setup scripts to be executed at the end

    """
    # --------------------------------------------------------------
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aLib, aInclude, aTopLevel, aVhdl2008, aFinalise):
        super(FileCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent)

        self.Lib = aLib
        self.Include = aInclude
        self.TopLevel = aTopLevel
        self.Vhdl2008 = aVhdl2008
        self.Finalise = aFinalise

    # --------------------------------------------------------------
    def __str__(self):

        lFlags = self.flags()
        return '{ \'%s\', flags: %s, component: \'%s:%s\' }' % (
            self.FilePath, ''.join(lFlags) if lFlags else 'none', self.Package, self.Component
        )

    # --------------------------------------------------------------
    def flags(self):
        lFlags = []
        if not self.Include:
            lFlags.append('noinclude')
        if self.TopLevel:
            lFlags.append('top')
        if self.Vhdl2008:
            lFlags.append('vhdl2008')
        if self.Finalise:
            lFlags.append('finalise')
        return lFlags

    __repr__ = __str__

    def __eq__(self, other):
        return (self.FilePath == other.FilePath) and (self.Lib == other.Lib)
    # --------------------------------------------------------------

class IncludeCommand(Command):
    """docstring for IncludeCommand"""
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aDepFileObj=None):
        super(IncludeCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent)
        self.depfile = aDepFileObj

# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Experimental
class DepFile(object):
    """docstring for DepFile"""
    def __init__(self, aPackage, aComponent, aName, aPath):
        super(DepFile, self).__init__()
        self.pkg = aPackage
        self.cmp = aComponent
        self.name = aName
        self.path = aPath
        self.entries = list()

        self.errors = list()
        self.unresolved = list()
        self.children = list()
        self.parents = list()

        self.locals = DictObj()

    # -----------------------------------------------------------------------------
    def __str__(self):
        pathmaker = Pathmaker.Pathmaker('', 1)
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

    def iterchildren(self):
        yield self
        for f in self.children:
            for sf in f.iterchildren():
                yield sf

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


# -----------------------------------------------------------------------------
class DepCmdParserError(Exception):
    pass


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

        subp = parser_add.add_parser('util')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='*')

        # Source sub-parser
        subp = parser_add.add_parser('src')
        subp.add_argument('-c', '--component', **lCompArgOpts)
        subp.add_argument('-l', '--lib')
        # subp.add_argument('-g', '--generated' , action = 'store_true') #
        # TODO: Check if still used in Vivado
        subp.add_argument('-n', '--noinclude', action='store_true')
        subp.add_argument('--cd')
        subp.add_argument('file', nargs='+')
        subp.add_argument('--vhdl2008', action='store_true')

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

        # --------------------------------------------------------------

    def parseLine(self, *args, **kwargs):

        return self.parse_args(*args, **kwargs)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class DepLineError(Exception):
    """Exception class for pre-parsing errors"""
    pass
# -----------------------------------------------------------------------------


class State(object):
    """Utility class that holds the current status of the parser
    while iterating through the tree of dependencies"""
    def __init__(self):
        super(State, self).__init__()
        self.depth = 0
        self.currentfile = None

    @property
    def tab(self):
        return ' ' * 4 * self.depth


# -----------------------------------------------------------------------------
class DepFileParser2g(object):
    """
    Dependency file parser class
    """
    @staticmethod
    def forwardparsing(aDepFileName):

        lFileTypes = {
            '.d3': True,
            '.dep': False,
        }
        return lFileTypes.get(splitext(aDepFileName)[1], True)

    # -----------------------------------------------------------------------------
    def __init__(self, aToolSet, aPathmaker, aVariables={}, aVerbosity=0):
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
        self.vars = dict()
        self.libs = set()
        self.components = OrderedDict()

        self.commands = {c: [] for c in ['setup', 'util', 'src', 'addrtab', 'iprepo']}

        self.missing = list()
        self.unresolved = list()
        self.errors = list()
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Add to or override the Script Variables with user commandline
        for lArgs in aVariables:
            lKey, lVal = lArgs.split('=')
            self.vars[lKey] = lVal
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set the toolset
        if self._toolset == 'xtclsh':
            self.vars['toolset'] = 'ISE'
        elif self._toolset == 'vivado':
            self.vars['toolset'] = 'Vivado'
        elif self._toolset == 'sim':
            self.vars['toolset'] = 'Modelsim'
        else:
            self.vars['toolset'] = 'other'
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set up the parser
        parser = DepCmdParser(usage=argparse.SUPPRESS)

        self.parseLine = parser.parseLine
        # --------------------------------------------------------------
    # -----------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    def _lineDropComments(self, aLine):
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
    def _lineProcessAssignments(self, aLine):
        # Process the assignment directive
        if aLine[0] != "@":
            return aLine

        # Process the assignment directive
        lTokenized = aLine[1:].split("=")
        if len(lTokenized) != 2:
            raise DepLineError("@ directives must be key=value pairs")
        if lTokenized[0].strip() in self.vars:
            print("Warning!", lTokenized[0].strip(
            ), "already defined. Not redefining.")
        else:
            try:
                exec(aLine[1:], None, self.vars)
            except Exception as lExc:
                raise_from(DepLineError("Parsing directive failed"), lExc)

        if self._verbosity > 1:
            print(self._state.tab, ':', aLine)

        # Return None (i.e. continue)
        return

    # -------------------------------------------------------------------------
    def _lineProcessConditional(self, aLine):
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
                aLine[lTokens[0] + 1: lTokens[1]], None, self.vars)
        except Exception as lExc:
            raise_from(DepLineError("Parsing directive failed"), lExc)

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
    def _lineReplaceVars(self, aLine):
        try:
            lLine = Template(aLine).substitute(self.vars)
        except RuntimeError as lExc:
            raise_from(DepLineError("Template substitution failed"), lExc)

        return lLine

    # -------------------------------------------------------------------------
    def _resolvePaths(self, aParsedLine, aDepFilePath, aPackage, aComponent):

        # --------------------------------------------------------------
        # Set package and module variables, whether specified or not
        lPackage, lComponent = aParsedLine.component

        # --------------------------------------------------------------
        # Set package and component to current ones if not defined
        if lPackage is None:
            lPackage = aPackage

        if lComponent is None:
            lComponent = aComponent
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set the target file expression, whether specified explicitly
        # or not
        if (not aParsedLine.file):
            lComponentName = lComponent.split('/')[-1]
            lFileExprList = [self._pathMaker.getDefName(
                aParsedLine.cmd, lComponentName)]
        else:
            lFileExprList = aParsedLine.file
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Expand file espression into a list of files
        lFileLists = list()
        lUnmatchedExprs = list()
        for lFileExpr in lFileExprList:
            # Expand file expression
            lPathExpr, lFileList = self._pathMaker.glob(
                lPackage, lComponent, aParsedLine.cmd, lFileExpr, cd=aParsedLine.cd
            )

            # --------------------------------------------------------------
            # Store the result and move on
            if lFileList:
                lFileLists.append(lFileList)
            else:
                lUnmatchedExprs.append(lPathExpr)

        return lFileLists, lUnmatchedExprs

    def _finalise(self, aParsedLine, aFileLists, aPackage, aComponent):

        # --------------------------------------------------------------
        # Set package and module variables, whether specified or not
        lPackage, lComponent = aParsedLine.component

        # --------------------------------------------------------------
        # Set package and component to current ones if not defined
        if lPackage is None:
            lPackage = aPackage

        if lComponent is None:
            lComponent = aComponent
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # If an include command, parse the specified dep files
        lEntries = list()
        if aParsedLine.cmd == "include":

            for lFileList in aFileLists:
                for lFile, lFilePath in lFileList:
                    lEntries.append(IncludeCommand(aParsedLine.cmd, lFilePath, aPackage, aComponent, self._parseFile(aPackage, aComponent, lFile)))
        else:
            # --------------------------------------------------------------
            lInclude = ('noinclude' not in aParsedLine) or (not aParsedLine.noinclude)
            lTopLevel = ('toplevel' in aParsedLine and aParsedLine.toplevel)
            lFinalise = ('finalise' in aParsedLine and aParsedLine.finalise)

            # --------------------------------------------------------------
            # Set the target library, whether specified explicitly or not
            lLib = aParsedLine.lib if ('lib' in aParsedLine) and (aParsedLine.lib) else None

            # --------------------------------------------------------------
            # Specifies the files should be read as VHDL 2008
            lVhdl2008 = aParsedLine.vhdl2008 if aParsedLine.cmd == 'src' else False

            for lFileList in aFileLists:
                for lFile, lFilePath in lFileList:
                    # --------------------------------------------------------------
                    # Debugging
                    if self._verbosity > 0:
                        print(self._state.tab, ' ',
                              aParsedLine.cmd, lFile, lFilePath)
                    # --------------------------------------------------------------

                    lEntries.append(FileCommand(aParsedLine.cmd, lFilePath, aPackage, aComponent, lLib, lInclude, lTopLevel, lVhdl2008, lFinalise))

        return lEntries
        # --------------------------------------------------------------

    # -------------------------------------------------------------------------
    def _parseFile(self, aPackage, aComponent, aDepFileName):

        lDepFilePath = self._pathMaker.getPath(
            aPackage, aComponent, 'include', aDepFileName)

        if lDepFilePath in self._depregistry:
            return self._depregistry[lDepFilePath]

        if self._verbosity > 1:
            print('>' * self._state.depth, 'Parsing',
                  aPackage, aComponent, aDepFileName)

        # This shouldn't be needed, already covered by the 
        if not exists(lDepFilePath):
            self.missing.append(
                (lDepFilePath, 'include', aPackage, aComponent, lDepFilePath))
            raise OSError("File " + lDepFilePath + " does not exist")

        # Ok, this is a new file. Let's dig in
        self._state.depth += 1

        lCurrentFile = DepFile(aPackage, aComponent, aDepFileName, lDepFilePath)
        self._depregistry[lDepFilePath] = lCurrentFile

        with open(lDepFilePath) as lDepFile:
            for lLineNr, lLine in enumerate(lDepFile):

                # --------------------------------------------------------------
                # Pre-processing
                try:
                    # Sanitize/drop comments
                    lLine = self._lineDropComments(lLine)
                    if not lLine:
                        continue

                    # Process variable assignment directives
                    lLine = self._lineProcessAssignments(lLine)
                    if not lLine:
                        continue

                    # Process conditional directives
                    lLine = self._lineProcessConditional(lLine)
                    if not lLine:
                        continue

                    # Replace variables
                    lLine = self._lineReplaceVars(lLine)

                except DepLineError as lExc:
                    lCurrentFile.errors.append((aPackage, aComponent, aDepFileName, lLineNr, lExc))
                    # raise_from(RuntimeError("Parsing failed in {0}, line {1}: {2}\n{3}".format(lDepFilePath, lLineNr, lExc.message, lLine)), lExc)
                    continue

                # --------------------------------------------------------------
                # Parse the line using arg_parse
                try:
                    lParsedLine = self.parseLine(lLine.split())
                except DepCmdParserError as lExc:
                    lCurrentFile.errors.append((aPackage, aComponent, aDepFileName, lLineNr, lExc))
                    # raise_from(RuntimeError("Parsing failed in {0}, line {1}: {2}\n{3}".format(lDepFilePath, lLineNr, lExc.message, lLine)), lExc)
                    # lMsg = "Error caught while parsing line {0} in file {1}".format(lLineNr, lDepFilePath) + "\n"
                    # lMsg += "Details - " + str(lExc) + ": '" + lLine + "'"
                    # raise RuntimeError(lMsg)
                    continue

                if self._verbosity > 1:
                    print(self._state.tab, '- Parsed line', vars(lParsedLine))

                lFileLists, lUnresolvedExpr = self._resolvePaths(lParsedLine, lDepFilePath, aPackage, aComponent)
                lCurrentFile.unresolved += [ (lExpr, lParsedLine.cmd, aPackage, aComponent, lDepFilePath) for lExpr in lUnresolvedExpr]

                lEntries = self._finalise(lParsedLine, lFileLists, aPackage, aComponent)
                lCurrentFile.entries += lEntries
                if lParsedLine.cmd == 'include':
                    for inc in lEntries:
                        lCurrentFile.children.append(inc.depfile)

                if self._verbosity > 1:
                    print(self._state.tab, '  -- Entries of', aDepFileName, ':', lEntries)

        if not self.forwardparsing(aDepFileName):
            lCurrentFile.entries.reverse()

        if self._verbosity > 1:
            print(self._state.tab, lCurrentFile)

            print('<' * self._state.depth)
        self._state.depth -= 1

        # TODO
        # Add me to the file registry
        return lCurrentFile

    # -------------------------------------------------------------------------
    def parse(self, aPackage, aComponent, aDepFileName):

        self._state = State()

        self.depfile = self._parseFile(aPackage, aComponent, aDepFileName)

        # --------------------------------------------------------------
        # If we are exiting the top-level, uniquify the commands list, keeping
        # the order as defined in Dave's origianl voodoo
        if self._state.depth != 0:
            raise RuntimeError("Something went wrong")
        self._state = None


        # fill up parsr results
        for c in self.depfile.itercmd():
            if self._verbosity > 0:
                print (c)
            self.commands[c.cmd].append(c)
            self.components.setdefault(
                c.Package, []).append(c.Component)
            if c.Lib is not None:
                self.libs.add(c.Lib)

        print ('>>>>')
        # Gather undresolved files and errors
        for dp, f in iteritems(self._depregistry):
            self.errors.extend(f.errors)
            self.unresolved.extend(f.unresolved)

        for i in self.commands:
            lTemp = list()
            for j in self.commands[i]:
                if j not in lTemp:
                    lTemp.append(j)
            self.commands[i] = lTemp

        # If we are exiting the top-level, uniquify the component list
        for lPkg in self.components:
            lTemp = list()
            lAdded = set()
            for lCmp in self.components[lPkg]:
                if lCmp not in lAdded:
                    lTemp.append(lCmp)
                    lAdded.add(lCmp)
            self.components[lPkg] = lTemp
        # --------------------------------------------------------------

    # -------------------------------------------------------------------------
