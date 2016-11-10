from __future__ import print_function
import argparse
import os
import glob

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Command(object):
  #--------------------------------------------------------------
  def __init__( self , aFilePath, aLib, aMap, aInclude , aTopLevel , aComponentPath, aVhdl2008 ):
    self.FilePath = aFilePath
    self.Lib = aLib
    self.Map = aMap
    self.Include = aInclude
    self.TopLevel = aTopLevel
    self.ComponentPath = aComponentPath
    self.Vhdl2008 = aVhdl2008

  def __str__(self):
    return str(self.__dict__)

  __repr__ = __str__

  def __eq__(self, other):
    return (self.FilePath == other.FilePath) and (self.Lib == other.Lib)
  #--------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class ComponentAction(argparse.Action):
  '''
  Parses <module>:<component>
  '''
  def __call__(self, parser, namespace, values, option_string=None):
    lSeparators = values.count(':')
    # Validate the format
    if lSeparators > 1:
      raise argparse.ArgumentTypeError('Malformed component name : %s. Expected <module>:<component>' % aComponentPath)
    
    lTokenized = values.split(':')
    if len(lTokenized) == 1:
      lTokenized.insert(0, None)

    setattr(namespace, self.dest, tuple(lTokenized) )
#------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class DepFileParser(object):
  #----------------------------------------------------------------------------------------------------------------------------
  def __init__( self , aCommandLineArgs , aPathmaker ):
    #--------------------------------------------------------------
    # Member variables
    self.CommandLineArgs = aCommandLineArgs
    self.Pathmaker = aPathmaker
    self.depth = 0

    self.ScriptVariables = {}
    self.ComponentIds = list()
    self.CommandList = {"setup": [], "src": [], "addrtab": [] , "cgpfile" : [] }
    self.Libs = list()
    self.Maps = list()
    self.FilesNotFound = list()
    #---
    self.Packages = list()
    self.PackagesNotFound = list()
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Add to or override the Script Variables with user commandline
    for lArgs in self.CommandLineArgs.define:
      lKey , lVal = lArgs.split('=')
      self.ScriptVariables[ lKey ] = lVal
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Set the toolset
    if self.CommandLineArgs.product == 'xtclsh':
      self.ScriptVariables[ "toolset" ] = "ISE"
    elif self.CommandLineArgs.product == 'vivado':
      self.ScriptVariables[ "toolset" ] = "Vivado"
    elif self.CommandLineArgs.product == 'sim' or self.CommandLineArgs.product == 'ip':
      self.ScriptVariables[ "toolset" ] = "Modelsim"
    else:
      self.ScriptVariables[ "toolset" ] = "other"
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Special options
    lCompArgOpts = dict( action=ComponentAction, default=(None, None) )
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Set up the parser
    parser = argparse.ArgumentParser(usage = argparse.SUPPRESS)
    parser_add = parser.add_subparsers(dest = "cmd")
    subp = parser_add.add_parser("include")
    subp.add_argument("-c","--component", **lCompArgOpts )
    subp.add_argument("--cd")
    subp.add_argument("file", nargs = "*")
    subp = parser_add.add_parser("setup")
    subp.add_argument("-c","--component", **lCompArgOpts )
    subp.add_argument("-z","--coregen", action = "store_true")
    subp.add_argument("--cd")
    subp.add_argument("file", nargs = "*")
    subp = parser_add.add_parser("src")
    subp.add_argument("-c", "--component", **lCompArgOpts )
    # subp.add_argument("-l", "--lib")
    # subp.add_argument("-m", "--map")
    # subp.add_argument("-g", "--generated" , action = "store_true") # TODO: Check if still used in Vivado
    subp.add_argument("-n", "--noinclude" , action = "store_true")
    subp.add_argument("--cd")
    subp.add_argument("file", nargs = "+")
    subp.add_argument("--vhdl2008" , action = "store_true")
    subp = parser_add.add_parser("addrtab")
    subp.add_argument("-c","--component", **lCompArgOpts )
    subp.add_argument("--cd")
    subp.add_argument("-t","--toplevel" , action = "store_true")
    subp.add_argument("file", nargs = "*")
    self.parseLine = parser.parse_args
    #--------------------------------------------------------------
  #----------------------------------------------------------------------------------------------------------------------------
  
  #----------------------------------------------------------------------------------------------------------------------------
  def parse(self, aPackage, aComponent, aDepFileName):
    '''
    Parses a dependency file from package aPackage/aComponent
    '''
    #--------------------------------------------------------------
    # We have gone one layer further down the rabbit hole
    self.depth += 1
    #--------------------------------------------------------------
    if self.CommandLineArgs.verbosity > 1:
      print('>'*self.depth,'Parsing', aPackage, aComponent, aDepFileName)
    
    #--------------------------------------------------------------
    lDepFilePath = self.Pathmaker.getPath( aPackage, aComponent, 'include', aDepFileName )
    #--------------------------------------------------------------
    
    with open(lDepFilePath) as lDepFile:
      for lLine in lDepFile:

        lLine = lLine.strip()
        #--------------------------------------------------------------
        # Ignore blank lines and comments
        if lLine == "" or lLine[0] == "#": continue
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Process the assignment directive
        if lLine[0] == "@":
          lTokenized = lLine[ 1: ].split( "=" )
          if len(lTokenized) != 2:
            raise SystemExit( "@ directives must be key=value pairs. Found '{0}' in {1}".format( lLine , aFileName ) )
          if lTokenized[0].strip() in self.ScriptVariables:
            print( "Warning!" , lTokenized[0].strip() , "already defined. Not redefining." )
          else:
            try:
              exec( lLine[ 1: ] , None , self.ScriptVariables )
            except:
              raise SystemExit( "Parsing directive failed in {0} , line '{1}'".format( aFileName , lLine ) )
          continue
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Process the conditional directive
        if lLine[0] == "?":
          lTokens = [ i for i, letter in enumerate(lLine) if letter == "?" ]
          if len(lTokens) != 2:
            raise SystemExit( "There must be precisely two '?' tokens per line. Found {0} in {1} , line '{2}'".format( len(lTokens) , aFileName , lLine ) )

          try:
            lExprValue = eval( lLine[ lTokens[0]+1 : lTokens[1] ] , None , self.ScriptVariables )
          except:
            raise SystemExit( "Parsing directive failed in {0} , line '{1}'".format( aFileName , lLine ) )

          if not isinstance( lExprValue , bool ):
            raise SystemExit( "Directive does not evaluate to boolean type in {0} , line '{1}'".format( aFileName , lLine ) )

          if not lExprValue:
            continue

          lLine = lLine[ lTokens[1]+1 : ].strip() # if line is accepted, strip the conditionality from the front and carry on
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Parse the line using arg_parse
        lParsedLine = self.parseLine(lLine.split())
        if self.CommandLineArgs.verbosity > 1:
          print(' '*self.depth, '- Parsed line', vars(lParsedLine))
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Set package and module variables, whether specified or not
        lPackage,lComponent = lParsedLine.component

        #--------------------------------------------------------------
        # Store package name, if exists. Continue otherwise
        if lPackage is None:
          lPackage = aPackage
        else:
          if not self.Pathmaker.packageExists(lPackage):
            self.PackagesNotFound.append(lPackage)
            continue

          if lPackage not in self.Packages:
            self.Packages.append(lPackage)
        #--------------------------------------------------------------
        
        #--------------------------------------------------------------
        # Store component paths
        if lComponent is None:
          lComponent = aComponent

        lComponentId = (lPackage, lComponent)
        if lComponentId not in self.ComponentIds:
          self.ComponentIds.append( lComponentId )
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Set the target file expression, whether specified explicitly or not
        if (not lParsedLine.file):
          lComponentName = lComponent.split('/')[-1]
          lFileExprList = [ self.Pathmaker.getDefName( lParsedLine.cmd , lComponentName ) ]
        else:
          lFileExprList = lParsedLine.file
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        #
        lType = lParsedLine.cmd
        #--------------------------------------------------------------


        #--------------------------------------------------------------
        # Set some processing flags, whether specified explicitly or not
        if 'noinclude' in lParsedLine:
          lInclude = not lParsedLine.noinclude
        else:
          lInclude = True

        if 'toplevel' in lParsedLine:
          lTopLevel = lParsedLine.toplevel
        else:
          lTopLevel = False
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Specifies the files should be read as VHDL 2008
        if lParsedLine.cmd == 'src' or lParsedLine.cmd == 'include' in lParsedLine:
          lVhdl2008 = lParsedLine.vhdl2008
        else:
          lVhdl2008 = False
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Debugging
        if self.CommandLineArgs.verbosity > 1:
          print(' '*self.depth, lPackage, lComponent, lFileExprList)
        #--------------------------------------------------------------
        
        for lFileExpr in lFileExprList:
          # Expand file expression
          lPathExpr, lFileList = self.Pathmaker.glob( lPackage, lComponent, lParsedLine.cmd , lFileExpr , cd = lParsedLine.cd )

          #--------------------------------------------------------------
          # Warn if something looks odd
          if not lFileList:
            self.FilesNotFound.append( lPath )
          #--------------------------------------------------------------

          for lFile, lFilePath in lFileList:
            #--------------------------------------------------------------
            # Debugging
            if self.CommandLineArgs.verbosity > 0:
              print(' ' * self.depth, ':', lParsedLine.cmd, lFileExpr, lFilePath, os.path.exists(lFilePath))
            #--------------------------------------------------------------
            
            #--------------------------------------------------------------
            # If an include command, parse the specified dep file, otherwise add the command to the command list
            if lParsedLine.cmd == "include":
              self.parse(lPackage, lComponent, lFile)
            else:

              # # Map to any generated libraries
              # if ('map' in lParsedLine) and (lParsedLine.map):
              #   lMap = lParsedLine.map
              #   self.Maps.append((lMap, lFile))
              # else:
              #   lMap = None

              # self.CommandList[ lType ].append( Command( lFile, lLib, lMap, lInclude , lTopLevel , lComponentPath, lVhdl2008 ) )
              self.CommandList[ lType ].append( Command( lFilePath, None, None, lInclude , lTopLevel , lComponentId, lVhdl2008 ) )
            #--------------------------------------------------------------
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # We are about to return one layer up the rabbit hole
    if self.CommandLineArgs.verbosity > 1:
      print('<'*self.depth)
    self.depth -= 1
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # If we are exiting the top-level, uniquify the commands list, keeping the order as defined in Dave's origianl voodoo
    if self.depth==0:
      for i in self.CommandList:
        lTemp = list()
        for j in reversed( self.CommandList[i] ):
          if not j in lTemp:
            lTemp.append(j)
        lTemp.reverse()
        self.CommandList[i] = lTemp
    #--------------------------------------------------------------

    
  #----------------------------------------------------------------------------------------------------------------------------
