from __future__ import print_function, absolute_import
from future.utils import raise_from
from future.utils import iterkeys, itervalues, iteritems

import argparse
import os
import glob
import copy
import string

from .definitions import depfiletypes
from ._pathmaker import Pathmaker
from ._cmdparser import ComponentAction, DepCmdParser, DepCmdParserError
from ._cmdtypes import SrcCommand, IncludeCommand
from ..tools.alien import AlienTree, AlienTemplate

from collections import OrderedDict
from os.path import exists, splitext, sep
# from string import Template




# -----------------------------------------------------------------------------
def _copyUpdateCommand(aCmd, aFilePath, aPkg, aCmp):
    """
    Utility function to update parsed commands
    """
    cmd = copy.deepcopy(aCmd)
    cmd.filepath = aFilePath
    cmd.package = aPkg
    cmd.component = aCmp
    return cmd

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
class DepLineError(Exception):
    """Exception class for pre-parsing errors"""
    pass
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
class DepFileParser(object):
    """
    Dependency file parser class
    """
    # -----------------------------------------------------------------------------
    @staticmethod
    def forwardparsing(aDepFileName):

        ftype = depfiletypes.get(splitext(aDepFileName)[1], None)
        if ftype is not None:
            return ftype['fwd']
        return True

    @property
    def rootdir(self):
        return self._pathMaker._rootdir

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
        self.config = AlienTree()
        self.libs = set()
        self.packages = OrderedDict()

        self.commands = {c: [] for c in ['setup', 'util', 'src', 'hlssrc', 'addrtab', 'iprepo']}

        self.unresolved = list()
        self.errors = list()
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Add to or override the Script Variables with user commandline
        for lArgs in aVariables:
            lKey, lVal = lArgs.split('=')
            self.config[lKey] = lVal
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set the toolset
        if self._toolset == 'vivado':
            self.config['toolset'] = 'Vivado'
        elif self._toolset == 'vivadohls':
            self.config['toolset'] = 'VivadoHls'
        elif self._toolset == 'sim':
            self.config['toolset'] = 'Modelsim'
        else:
            self.config['toolset'] = 'other'
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set up the parser
        parser = DepCmdParser(usage=argparse.SUPPRESS)

        self.parseLine = parser.parseLine
        # --------------------------------------------------------------
    # -----------------------------------------------------------------------------

    # -----------------------------------------------------------------------------
    @property
    def unresolvedPaths(self):
        lNotFound = set()

        for lPathExpr, aCmd, lPackage, lComponent, lDepFilePath, lDepPackage, lDepComponent in self.unresolved:
            lNotFound.add(lPathExpr)

        return lNotFound
    # -----------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    @property
    def unresolvedPackages(self):
        lNotFound = set()

        for lPathExpr, lCmd, lPackage, lComponent, lDepPackage, lDepComponent, lDepFilePath in self.unresolved:
            if os.path.exists(self._pathMaker.getPath(lPackage)):
                continue

            lNotFound.add(lPackage)
        return lNotFound

    # -------------------------------------------------------------------------
    @property
    def unresolvedComponents(self):
        lNotFound = OrderedDict()

        for lPathExpr, lCmd, lPackage, lComponent, lDepPackage, lDepComponent, lDepFilePath in self.unresolved:
            if os.path.exists(self._pathMaker.getPath(lPackage, lComponent)):
                continue

            lNotFound.setdefault(lPackage, set()).add(lComponent)

        return lNotFound

    # -----------------------------------------------------------------------------
    @property
    def unresolvedFiles(self):
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

        if aLine.count(';'):
            raise DepLineError("Semicolons (;) are not allowed")

        # Process the assignment directive
        lTokens = aLine[1:].split("=")
        if len(lTokens) != 2:
            raise DepLineError("@ directives must be key=value pairs")

        lPar, lExpr = map(string.strip, lTokens)

        if lPar.strip() in self.config:
            print("Warning!", lPar.strip(
            ), "already defined. Not redefining.")
        else:
            try:
                # exec(aLine[1:], None, self.config)
                lOldLock = self.config.locked
                self.config.lock(True)
                x = eval(lExpr, None, self.config)
                self.config.lock(lOldLock)
                self.config[lPar] = x

            except Exception as lExc:
                raise_from(DepLineError("VariableAssignmentError"), lExc)
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
                aLine[lTokens[0] + 1: lTokens[1]], None, self.config
            )
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
            lLine = AlienTemplate(aLine).substitute(self.config)
        except RuntimeError as lExc:
            raise_from(DepLineError("Template substitution failed"), lExc)

        return lLine

# -------------------------------------------------------------------------
    def _resolvePaths(self, aParsedCmd, aDepFilePath, aCurPackage, aCurComponent):

        # --------------------------------------------------------------
        # Set package and component to current ones if not defined
        lPackage = aParsedCmd.package if aParsedCmd.package else aCurPackage
        lComponent = aParsedCmd.component if aParsedCmd.component else aCurComponent
        # --------------------------------------------------------------

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
                lUnmatchedExprs = [self._pathMaker.getDefNames(aParsedCmd.cmd, lComponentName, 'braces')]
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
                cmd = _copyUpdateCommand(aParsedCmd, lFilePath, lPackage, lComponent)
                # If an include command, parse the sub-dep files
                if aParsedCmd.cmd == "include":
                    cmd.depfile = self._parseFile(lPackage, lComponent, lFile)
                lEntries.append(cmd)


        return lEntries, (lUnmatchedExprs, lPackage, lComponent)
        # --------------------------------------------------------------

    # -------------------------------------------------------------------------
    def _parseFile(self, aPackage, aComponent, aDepFileName):
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

        # This shouldn't be needed, already covered by the 
        if not exists(lDepFilePath):
            self.unresolved.append(
                (lDepFilePath, 'include', aPackage, aComponent, '__top__', '__top__', '__top__'))
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
                    lCurrentFile.errors.append((aPackage, aComponent, aDepFileName, lDepFilePath, lLineNr, lLine, lExc))
                    continue

                # --------------------------------------------------------------
                # Parse the line using arg_parse
                try:
                    lParsedCmd = self.parseLine(lLine.split())
                except DepCmdParserError as lExc:
                    lCurrentFile.errors.append((aPackage, aComponent, aDepFileName, lDepFilePath, lLineNr, lLine, lExc))
                    continue

                if self._verbosity > 1:
                    print(self._state.tab, '- Parsed line', vars(lParsedCmd))

                # --------------------------------------------------------------
                lEntries, (lUnresolvedExpr, lParsedPackage, lParsedComponent) = self._resolvePaths(lParsedCmd, lDepFilePath, aPackage, aComponent)
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

        # TODO: create a reset method
        self._state = State()

        # Do the parsing here
        self.depfile = self._parseFile(aPackage, aComponent, aDepFileName)

        # Lock the config variables tree
        self.config.lock(True)
        # --------------------------------------------------------------
        # If we are exiting the top-level, uniquify the commands list, keeping
        # the order as defined in Dave's origianl voodoo
        if self._state.depth != 0:
            raise RuntimeError("Something went wrong")
        self._state = None

        # Collect summary information
        for lCmd in self.depfile.itercmd():
            if self._verbosity > 0:
                print (lCmd)
            self.commands[lCmd.cmd].append(lCmd)
            self.packages.setdefault(
                lCmd.package, []).append(lCmd.component)
            if isinstance(lCmd, SrcCommand) and lCmd.lib is not None:
                self.libs.add(lCmd.lib)

        # Gather unresolved files and errors
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
        for lPkg in self.packages:
            lTemp = list()
            lAdded = set()
            for lCmp in self.packages[lPkg]:
                if lCmp not in lAdded:
                    lTemp.append(lCmp)
                    lAdded.add(lCmp)
            self.packages[lPkg] = lTemp
        # --------------------------------------------------------------

    # -------------------------------------------------------------------------


class DepFormatter(object):
    """docstring for DepFormatter"""
    def __init__(self, aParser):
        super(DepFormatter, self).__init__()
        self.parser = aParser

    # -----------------------------------------------------------------------------
    def reportCommands(self):
        lPrsr = self.parser
        lOutTxt = ''
        lOutTxt += 'Commands\n'
        lOutTxt += '--------\n'
        for k in lPrsr.commands:
            lOutTxt += '+ %s (%d)\n' % (k, len(lPrsr.commands[k]))
            for lCmd in lPrsr.commands[k]:
                lOutTxt += '  * ' + str(lCmd) + '\n'
        return lOutTxt

    # -----------------------------------------------------------------------------
    def reportPackages(self):
        lPrsr = self.parser
        lOutTxt = ''
        lOutTxt += 'Resolved packages & components\n'
        lOutTxt += '------------------------------\n'
        lOutTxt += 'packages: ' + ', '.join(iterkeys(lPrsr.packages)) + '\n'
        lOutTxt += 'components:\n'
        for pkg in sorted(lPrsr.packages):
            lOutTxt += '+ %s (%d)\n' % (pkg, len(lPrsr.packages[pkg]))
            for cmp in sorted(lPrsr.packages[pkg]):
                lOutTxt += '  > ' + str(cmp if cmp else '<root>') + '\n'
        return lOutTxt

    # -----------------------------------------------------------------------------
    def reportUnresolved(self):
        lPrsr = self.parser
        lOutTxt = ''
        lOutTxt += 'Missing packages, components & files\n'
        lOutTxt += '------------------------------------\n'

        lUPkgs = lPrsr.unresolvedPackages
        if lUPkgs:
            lOutTxt += 'packages: ' + \
                str(list(self.lUPkgs)) + '\n'

        lUCmp = lPrsr.unresolvedComponents
        if lUCmp:
            lOutTxt += 'components: \n'

            for pkg in sorted(lUCmp):
                lOutTxt += '+ %s (%d)\n' % (pkg, len(lUCmp[pkg]))

                for cmp in sorted(lUCmp[pkg]):
                    lOutTxt += '  > ' + str(cmp) + '\n'

        lUFl = lPrsr.unresolvedFiles
        if lUFl:
            lOutTxt += 'files:\n'

            for pkg in sorted(lUFl):
                lCmps = lUFl[pkg]
                lOutTxt += '+ %s (%d components)\n' % (pkg, len(lCmps))

                for cmp in sorted(lCmps):
                    lFiles = lCmps[cmp]
                    lOutTxt += '  + %s (%d files)\n' % (cmp, len(lFiles))

                    lCmpPath = lPrsr._pathMaker.getPath(pkg, cmp)
                    for lFile in sorted(lFiles):
                        lSrcs = lFiles[lFile]
                        lOutTxt += '    + %s\n' % os.path.relpath(
                            lFile, lCmpPath)
                        lOutTxt += '      | included by %d dep file(s)\n' % len(
                            lSrcs)

                        for lSrc in lSrcs:
                            lOutTxt += '      \\ - %s\n' % os.path.relpath(
                                lSrc, lPrsr.rootdir)
                        lOutTxt += '\n'
        return lOutTxt

    # -----------------------------------------------------------------------------
    def summary(self):

        lOutTxt = ''
        lOutTxt += self.reportCommands()

        lOutTxt += '\n'
        lOutTxt += self.reportPackages()

        if self.parser.unresolved:
            lOutTxt += '\n'
            lOutTxt += self.reportUnresolved()
            return lOutTxt

        return lOutTxt
    # -----------------------------------------------------------------------------

