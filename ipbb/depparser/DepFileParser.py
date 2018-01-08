from __future__ import print_function
import argparse
import os
import glob
from collections import OrderedDict
from os.path import exists

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


class Command(object):
    # --------------------------------------------------------------
    def __init__(self, aFilePath, aPackage, aComponent, aLib, aMap, aInclude, aTopLevel, aVhdl2008):
        self.FilePath = aFilePath
        self.Package = aPackage
        self.Component = aComponent
        self.Lib = aLib
        self.Map = aMap
        self.Include = aInclude
        self.TopLevel = aTopLevel
        self.Vhdl2008 = aVhdl2008

    def __str__(self):
        # return str(self.__dict__)

        lFlags = []
        if not self.Include:
            lFlags.append('noinclude')
        if self.TopLevel:
            lFlags.append('top')
        if self.Vhdl2008:
            lFlags.append('vhdl2008')
        return '{ \'%s\', flags: %s, component: \'%s:%s\' }' % (
            self.FilePath, ''.join(lFlags) if lFlags else 'none', self.Package, self.Component
        )

    def flags(self):
        lFlags = []
        if not self.Include:
            lFlags.append('noinclude')
        if self.TopLevel:
            lFlags.append('top')
        if self.Vhdl2008:
            lFlags.append('vhdl2008')
        return lFlags
        
    __repr__ = __str__

    def __eq__(self, other):
        return (self.FilePath == other.FilePath) and (self.Lib == other.Lib)
    # --------------------------------------------------------------
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
class DepLineParserError(Exception):
    pass


class DepLineParser(argparse.ArgumentParser):
    def error(self, message):
        raise DepLineParserError(message)
# ------------------------------------------------------------------------------


class DepFileParser(object):
    # ----------------------------------------------------------------------------------------------------------------------------
    def __init__(self, aToolSet, aPathmaker, aVariables={}, aVerbosity=0):
        # --------------------------------------------------------------
        # Member variables
        self._toolset = aToolSet
        self._depth = 0
        self._verbosity = aVerbosity
        self.Pathmaker = aPathmaker

        self.ScriptVariables = {}
        self.CommandList = {'setup': [], 'src': [],
                            'addrtab': [], 'cgpfile': []}
        self.Libs = list()
        self.Maps = list()
        self.Components = OrderedDict()

        self.NotFound = list()
        self.DepMap = {}
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Add to or override the Script Variables with user commandline
        for lArgs in aVariables:
            lKey, lVal = lArgs.split('=')
            self.ScriptVariables[lKey] = lVal
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set the toolset
        if self._toolset == 'xtclsh':
            self.ScriptVariables['toolset'] = 'ISE'
        elif self._toolset == 'vivado':
            self.ScriptVariables['toolset'] = 'Vivado'
        elif self._toolset == 'sim':
            self.ScriptVariables['toolset'] = 'Modelsim'
        else:
            self.ScriptVariables['toolset'] = 'other'
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Special options
        lCompArgOpts = dict(action=ComponentAction, default=(None, None))
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # Set up the parser
        parser = DepLineParser(usage=argparse.SUPPRESS)
        parser_add = parser.add_subparsers(dest="cmd")
        subp = parser_add.add_parser("include")
        subp.add_argument("-c", "--component", **lCompArgOpts)
        subp.add_argument("--cd")
        subp.add_argument("file", nargs="*")
        subp = parser_add.add_parser("setup")
        subp.add_argument("-c", "--component", **lCompArgOpts)
        subp.add_argument("-z", "--coregen", action="store_true")
        subp.add_argument("--cd")
        subp.add_argument("file", nargs="*")
        subp = parser_add.add_parser("src")
        subp.add_argument("-c", "--component", **lCompArgOpts)
        subp.add_argument("-l", "--lib")
        subp.add_argument("-m", "--map")
        # subp.add_argument("-g", "--generated" , action = "store_true") #
        # TODO: Check if still used in Vivado
        subp.add_argument("-n", "--noinclude", action="store_true")
        subp.add_argument("--cd")
        subp.add_argument("file", nargs="+")
        subp.add_argument("--vhdl2008", action="store_true")
        subp = parser_add.add_parser("addrtab")
        subp.add_argument("-c", "--component", **lCompArgOpts)
        subp.add_argument("--cd")
        subp.add_argument("-t", "--toplevel", action="store_true")
        subp.add_argument("file", nargs="*")

        # map parser method to self
        self.parseLine = parser.parse_args
        # --------------------------------------------------------------
    # ----------------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
    def __str__(self):
        string = ''
        #  self.__repr__() + '\n'
        string += '+------------+\n'
        string += '|  Commands  |\n'
        string += '+------------+\n'
        for k in self.CommandList:
            string += '+ %s (%d)\n' % (k, len(self.CommandList[k]))
            for lCmd in self.CommandList[k]:
                string += '  * ' + str(lCmd) + '\n'

        string += '\n'
        string += '+----------------------------------+\n'
        string += '|  Resolved packages & components  |\n'
        string += '+----------------------------------+\n'
        string += 'packages: ' + str(list(self.Components.iterkeys())) + '\n'
        string += 'components:\n'
        for pkg in sorted(self.Components):
            string += '+ %s (%d)\n' % (pkg, len(self.Components[pkg]))
            for cmp in sorted(self.Components[pkg]):
                string += '  > ' + str(cmp) + '\n'

        if self.NotFound:
            string += '\n'
            string += '+----------------------------------------+\n'
            string += '|  Missing packages, components & files  |\n'
            string += '+----------------------------------------+\n'

            if self.PackagesNotFound:
                string += 'packages: ' + \
                    str(list(self.PackagesNotFound)) + '\n'

            # ------
            lCNF = self.ComponentsNotFound
            if lCNF:
                string += 'components: \n'

                for pkg in sorted(lCNF):
                    string += '+ %s (%d)\n' % (pkg, len(lCNF[pkg]))

                    for cmp in sorted(lCNF[pkg]):
                        string += '  > ' + str(cmp) + '\n'
            # ------

            # ------
            lFNF = self.FilesNotFound
            if lFNF:
                string += 'missing files:\n'

                for pkg in sorted(lFNF):
                    lCmps = lFNF[pkg]
                    string += '+ %s (%d components)\n' % (pkg, len(lCmps))

                    for cmp in sorted(lCmps):
                        lFiles = lCmps[cmp]
                        string += '  + %s (%d files)\n' % (cmp, len(lFiles))

                        lCmpPath = self.Pathmaker.getPath(pkg, cmp)
                        for lFile in sorted(lFiles):
                            lSrcs = lFiles[lFile]
                            string += '    + %s\n' % os.path.relpath(
                                lFile, lCmpPath)
                            string += '      | included by %d dep file(s)\n' % len(
                                lSrcs)

                            for lSrc in lSrcs:
                                string += '      \ - %s\n' % os.path.relpath(
                                    lSrc, self.Pathmaker.rootdir)
                            string += '\n'
            # ------

        # string += '\n'.join([' > '+f for f in sorted(self.FilesNotFound)])
        return string
    # ----------------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
    @property
    def PathsNotFound(self):
        lNotFound = set()

        for lPathExpr, aCmd, lPackage, lComponent, lDepFilePath in self.NotFound:
            lNotFound.add(lPathExpr)

        return lNotFound
    # ----------------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
    @property
    def FilesNotFound(self):
        lNotFound = OrderedDict()
        for lPathExpr, aCmd, lPackage, lComponent, lDepFilePath in self.NotFound:
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
    # ----------------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
    @property
    def ComponentsNotFound(self):
        lNotFound = OrderedDict()

        for lPathExpr, aCmd, lPackage, lComponent, lDepFilePath in self.NotFound:
            if os.path.exists(self.Pathmaker.getPath(lPackage, lComponent)):
                continue

            lNotFound.setdefault(lPackage, set()).add(lComponent)

        return lNotFound
    # ----------------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
    @property
    def PackagesNotFound(self):
        lNotFound = set()

        for lPathExpr, aCmd, lPackage, lComponent, lDepFilePath in self.NotFound:
            if os.path.exists(self.Pathmaker.getPath(lPackage)):
                continue

            lNotFound.add(lPackage)
        return lNotFound
    # ----------------------------------------------------------------------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
    def parse(self, aPackage, aComponent, aDepFileName):
        '''
        Parses a dependency file from package aPackage/aComponent
        '''
        # --------------------------------------------------------------
        # We have gone one layer further down the rabbit hole
        self._depth += 1
        # --------------------------------------------------------------
        if self._verbosity > 1:
            print('>' * self._depth, 'Parsing',
                  aPackage, aComponent, aDepFileName)

        # --------------------------------------------------------------
        lDepFilePath = self.Pathmaker.getPath(
            aPackage, aComponent, 'include', aDepFileName)
        # --------------------------------------------------------------


        if not exists(lDepFilePath):
            self.NotFound.append(
                (lDepFilePath, 'include', aPackage, aComponent, lDepFilePath))
            raise IOError("File "+lDepFilePath+" does not exist")

        with open(lDepFilePath) as lDepFile:
            for lLineNum, lLine in enumerate(lDepFile):

                lLine = lLine.strip()
                # --------------------------------------------------------------
                # Ignore blank lines and comments
                if lLine == "" or lLine[0] == "#":
                    continue
                # --------------------------------------------------------------

                # --------------------------------------------------------------
                # Process the assignment directive
                if lLine[0] == "@":
                    lTokenized = lLine[1:].split("=")
                    if len(lTokenized) != 2:
                        raise SystemExit("@ directives must be key=value pairs. Found '{0}' in {1}".format(
                            lLine, aDepFileName))
                    if lTokenized[0].strip() in self.ScriptVariables:
                        print("Warning!", lTokenized[0].strip(
                        ), "already defined. Not redefining.")
                    else:
                        try:
                            exec(lLine[1:], None, self.ScriptVariables)
                        except:
                            raise SystemExit(
                                "Parsing directive failed in {0} , line '{1}'".format(aDepFileName, lLine))
                    continue
                # --------------------------------------------------------------

                # --------------------------------------------------------------
                # Process the conditional directive
                if lLine[0] == "?":
                    lTokens = [i for i, letter in enumerate(
                        lLine) if letter == "?"]
                    if len(lTokens) != 2:
                        raise SystemExit(
                            "There must be precisely two '?' tokens per line. Found {0} in {1} , line '{2}'".format(
                                len(lTokens), aDepFileName, lLine
                            )
                        )

                    try:
                        lExprValue = eval(
                            lLine[lTokens[0] + 1: lTokens[1]], None, self.ScriptVariables)
                    except:
                        raise SystemExit(
                            "Parsing directive failed in {0} , line '{1}'".format(aDepFileName, lLine))

                    if not isinstance(lExprValue, bool):
                        raise SystemExit("Directive does not evaluate to boolean type in {0} , line '{1}'".format(
                            aDepFileName, lLine))

                    if not lExprValue:
                        continue

                    # if line is accepted, strip the conditionality from the
                    # front and carry on
                    lLine = lLine[lTokens[1] + 1:].strip()
                # --------------------------------------------------------------

                # --------------------------------------------------------------
                # Parse the line using arg_parse
                try:
                    lParsedLine = self.parseLine(lLine.split())
                except DepLineParserError as e:
                    lMsg = "Error caught while parsine line {0} in file {1}".format(lLineNum,lDepFilePath) + "\n"
                    lMsg += "Details - " + e.message + ": '" + lLine + "'"
                    raise RuntimeError(lMsg)

                if self._verbosity > 1:
                    print(' ' * self._depth, '- Parsed line', vars(lParsedLine))
                # --------------------------------------------------------------

                # --------------------------------------------------------------
                # Set package and module variables, whether specified or not
                lPackage, lComponent = lParsedLine.component

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
                if (not lParsedLine.file):
                    lComponentName = lComponent.split('/')[-1]
                    lFileExprList = [self.Pathmaker.getDefName(
                        lParsedLine.cmd, lComponentName)]
                else:
                    lFileExprList = lParsedLine.file
                # --------------------------------------------------------------

                # --------------------------------------------------------------
                # Expand file espression into a list of files
                lFileLists = []
                for lFileExpr in lFileExprList:
                    # Expand file expression
                    lPathExpr, lFileList = self.Pathmaker.glob(
                        lPackage, lComponent, lParsedLine.cmd, lFileExpr, cd=lParsedLine.cd)

                    # --------------------------------------------------------------
                    # Store the result and move on
                    if lFileList:
                        lFileLists.append(lFileList)

                        self.Components.setdefault(
                            lPackage, []).append(lComponent)

                    else:
                        # Something's off, no files found
                        self.NotFound.append(
                            (lPathExpr, lParsedLine.cmd, lPackage, lComponent, lDepFilePath))
                    # --------------------------------------------------------------
                # --------------------------------------------------------------

                # --------------------------------------------------------------
                # If an include command, parse the specified dep files
                if lParsedLine.cmd == "include":
                    for lFileList in lFileLists:
                        for lFile, lFilePath in lFileList:
                            self.parse(lPackage, lComponent, lFile)

                else:
                    # --------------------------------------------------------------
                    # Set some processing flags, whether specified explicitly
                    # or not
                    if 'noinclude' in lParsedLine:
                        lInclude = not lParsedLine.noinclude
                    else:
                        lInclude = True

                    if 'toplevel' in lParsedLine:
                        lTopLevel = lParsedLine.toplevel
                    else:
                        lTopLevel = False
                    # --------------------------------------------------------------

                    # --------------------------------------------------------------
                    # Set the target library, whether specified explicitly or
                    # not
                    if ('lib' in lParsedLine) and (lParsedLine.lib):
                        lLib = lParsedLine.lib
                        self.Libs.append(lLib)
                    else:
                        lLib = None
                    # --------------------------------------------------------------

                    # --------------------------------------------------------------
                    # Specifies the files should be read as VHDL 2008
                    if lParsedLine.cmd == 'src' or lParsedLine.cmd == 'include' in lParsedLine:
                        lVhdl2008 = lParsedLine.vhdl2008
                    else:
                        lVhdl2008 = False
                    # --------------------------------------------------------------

                    for lFileList in lFileLists:
                        for lFile, lFilePath in lFileList:
                            # --------------------------------------------------------------
                            # Debugging
                            if self._verbosity > 0:
                                print(' ' * self._depth, ':',
                                      lParsedLine.cmd, lFile, lFilePath)
                            # --------------------------------------------------------------

                            # --------------------------------------------------------------
                            # Map to any generated libraries
                            if ('map' in lParsedLine) and (lParsedLine.map):
                                lMap = lParsedLine.map
                                self.Maps.append((lMap, lFilePath))
                            else:
                                lMap = None
                            # --------------------------------------------------------------

                            self.CommandList[lParsedLine.cmd].append(Command(
                                lFilePath, lPackage, lComponent, lMap, lInclude, lInclude, lTopLevel, lVhdl2008
                            ))

                            self.DepMap.setdefault(lFilePath, []).append(lDepFilePath)
                        # --------------------------------------------------------------
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # We are about to return one layer up the rabbit hole
        if self._verbosity > 1:
            print('<' * self._depth)
        self._depth -= 1
        # --------------------------------------------------------------

        # --------------------------------------------------------------
        # If we are exiting the top-level, uniquify the commands list, keeping
        # the order as defined in Dave's origianl voodoo
        if self._depth == 0:
            for i in self.CommandList:
                lTemp = list()
                for j in reversed(self.CommandList[i]):
                    if j not in lTemp:
                        lTemp.append(j)
                lTemp.reverse()
                self.CommandList[i] = lTemp

        # If we are exiting the top-level, uniquify the component list
            for lPkg in self.Components:
                lTemp = list()
                lAdded = set()
                for lCmp in self.Components[lPkg]:
                    if lCmp not in lAdded:
                        lTemp.append(lCmp)
                        lAdded.add(lCmp)
                self.Components[lPkg] = lTemp
        # --------------------------------------------------------------

    # ----------------------------------------------------------------------------------------------------------------------------
