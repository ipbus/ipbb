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

  def __eq__(self, other):
    return (self.FilePath == other.FilePath) and (self.Lib == other.Lib)
  #--------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



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
    self.ComponentPaths = list()
    self.CommandList = {"setup": [], "src": [], "addrtab": [] , "cgpfile" : [] }
    self.Libs = list()
    self.Maps = list()
    self.FilesNotFound = list()
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
    # Set up the parser
    parser = argparse.ArgumentParser(usage = argparse.SUPPRESS)
    parser_add = parser.add_subparsers(dest = "cmd")
    subp = parser_add.add_parser("include")
    subp.add_argument("-c","--component")
    subp.add_argument("--cd")
    subp.add_argument("file", nargs = "*")
    subp.add_argument("--vhdl2008" , action = "store_true")
    subp = parser_add.add_parser("setup")
    subp.add_argument("-c","--component")
    subp.add_argument("-z","--coregen", action = "store_true")
    subp.add_argument("--cd")
    subp.add_argument("file", nargs = "*")
    subp = parser_add.add_parser("src")
    subp.add_argument("-c", "--component")
    subp.add_argument("-l", "--lib")
    subp.add_argument("-m", "--map")
    subp.add_argument("-g", "--generated" , action = "store_true") # TODO: Check if still used in Vivado
    subp.add_argument("-n", "--noinclude" , action = "store_true")
    subp.add_argument("--cd")
    subp.add_argument("file", nargs = "+")
    subp.add_argument("--vhdl2008" , action = "store_true")
    subp = parser_add.add_parser("addrtab")
    subp.add_argument("-c","--component")
    subp.add_argument("--cd")
    subp.add_argument("-t","--toplevel" , action = "store_true")
    subp.add_argument("file", nargs = "*")
    self.parseLine = parser.parse_args
    #--------------------------------------------------------------
  #----------------------------------------------------------------------------------------------------------------------------

  #----------------------------------------------------------------------------------------------------------------------------
  def parse(self, aFileName, aComponentPath):

    #--------------------------------------------------------------
    # We have gone one layer further down the rabbit hole
    self.depth += 1
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Component path expected format <package>:<component>
    lSplitPath = self.Pathmaker.getcomppath(aComponentPath)
    if len(lSplitPath) != 2:
      raise SystemExit('Malformed component path %s. Expected format <package>:<component>' % aComponentPath )
    lPackage = lSplitPath[0]
    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # Open the dep file and iterate over it
    with open(aFileName) as lDepFile:
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
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Set the component path, whether specified explicitly or not
        if (lParsedLine.component is None):
          lComponentPath = aComponentPath
        else:
          lComponentPath = self.Pathmaker.normcomppath(lParsedLine.component, lPackage)
          if lComponentPath not in self.ComponentPaths:
            self.ComponentPaths.append(lComponentPath)
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Set the target file expression, whether specified explicitly or not
        if (not lParsedLine.file):
          lComponentName = lComponentPath.split('/')[-1]
          lFileExprList = [ self.Pathmaker.getdefname( lParsedLine.cmd , lComponentName ) ]
        else:
          lFileExprList = lParsedLine.file
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Set the target library, whether specified explicitly or not
        if ('lib' in lParsedLine) and (lParsedLine.lib):
          lLib = lParsedLine.lib
          self.Libs.append(lLib)
        else:
          lLib = None
        #--------------------------------------------------------------

        #--------------------------------------------------------------
        # Identify the command type
        if (lParsedLine.cmd == "setup") and ('coregen' in lParsedLine) and (lParsedLine.coregen):
          lType = "cgpfile"
        else:
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
          print(' '*self.depth,"***", lParsedLine, lComponentPath, lFileExprList)
        #--------------------------------------------------------------

        for lFileExpr in lFileExprList:
          #--------------------------------------------------------------
          # TODO: Check if still used in Vivado
          # If we are looking at generated files, look in the ipcore_dir, else look where we are told
          # if 'generated' in lParsedLine and lParsedLine.generated:
          #   lPath = self.Pathmaker.getrelpath( "ipcore_dir" , lFileExpr , lParsedLine.cd )
          #   lFileList = [ lPath ]
          # else:
          #   lPath = self.Pathmaker.getpath( lComponentPath , lParsedLine.cmd , lFileExpr , cd = lParsedLine.cd )
          #   lFileList = glob.glob( lPath )
          #--------------------------------------------------------------
          lPath = self.Pathmaker.getpath( lComponentPath , lParsedLine.cmd , lFileExpr , cd = lParsedLine.cd )
          lFileList = glob.glob( lPath )

          #--------------------------------------------------------------
          # Warn if something looks odd
          if not lFileList:
            self.FilesNotFound.append( lPath )
          #--------------------------------------------------------------

          for lFile in lFileList:
            #--------------------------------------------------------------
            # Debugging
            if self.CommandLineArgs.verbosity > 0:
              print("  " * self.depth, lParsedLine.cmd, lFileExpr, lFile, os.path.exists(lFile))
            #--------------------------------------------------------------

            #--------------------------------------------------------------
            # If an include command, parse the specified dep file, otherwise add the command to the command list
            if lParsedLine.cmd == "include":
              self.parse(lFile, lComponentPath)
            else:

              # Map to any generated libraries
              if ('map' in lParsedLine) and (lParsedLine.map):
                lMap = lParsedLine.map
                self.Maps.append((lMap, lFile))
              else:
                lMap = None

              self.CommandList[ lType ].append( Command( lFile, lLib, lMap, lInclude , lTopLevel , lComponentPath, lVhdl2008 ) )
            #--------------------------------------------------------------


    #--------------------------------------------------------------

    #--------------------------------------------------------------
    # We are about to return one layer up the rabbit hole
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

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
