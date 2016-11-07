from __future__ import print_function
import os

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Pathmaker(object):

  fpaths = {"src": "firmware/hdl", "include": "firmware/cfg", "addrtab": "addr_table", "setup": "firmware/cfg"}
  fexts = {"src": "vhd", "include": "dep", "addrtab": "xml" } #, "setup": "tcl"}

  #--------------------------------------------------------------
  # def __init__(self, rootdir, topdir, mapfile, verbosity):
  def __init__(self, rootdir, mapfile, verbosity):
    self.rootdir = rootdir
    # self.topdir = topdir
    self.verbosity = verbosity
    self.componentmap = None

    if self.verbosity > 2:
      print("+++ Pathmaker init", root, topdir, mapfile)

    if mapfile:
      self.componentmap = dict()
      with open(mapfile) as lFile:
        for lLine in lFile:
          lLine = lLine.strip()
          if lLine == "" or lLine[0] == "#": continue
          lTokenized = lLine.split()
          self.componentmap[ lTokenized[0] ] = lTokenized[1]
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getcomppath(self, componentname):
    # TODO: check if still make sense
    # if componentname == "ipcore_dir":
      # return "ipcore_dir"
    # elif componentname == "top":
      # return self.topdir

    # Resolve package name
    if componentname.count(':') > 1:
      raise SystemExit('Malformed component name : %s' % componentname)

    tokens = componentname.split(':')

    if self.componentmap is not None:
      tokens[-1] = componentmap[tokens[-1]]

    return tokens
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def normcomppath(self, componentname, componentpkg):
    tokens = self.getcomppath(componentname)
    if len(tokens) == 2:
      pass
    elif len(tokens) == 1:
      tokens.insert(0,componentpkg)

    return ':'.join(tokens)
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getdefname(self, kind, name):
    return "{0}.{1}".format( name , self.fexts[kind] )
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getpath(self, comp, kind = None, name = None, defext = False, cd = None): #descend = None, subdir = None
    path = self.getcomppath(comp)

    if kind:
      path.append( self.fpaths[kind] )

    if cd:
      path.append( cd )

    if name:
      if defext:
        path.append( self.getdefname(kind, name) )
      else:
        path.append( name )

    path2 = os.path.normpath( os.path.join( self.rootdir , *path ) )

    if self.verbosity > 2:
      print("+++ Pathmaker", comp, kind, name, defext, descend, subdir, path2)
    return path2
  #--------------------------------------------------------------

  #--------------------------------------------------------------
  def getrelpath(self, loc, name, cd = None):
    path = []

    if cd:
      path.append( cd )
    path.append(name)

    return os.path.normpath( os.path.join( loc , *path ) )
  #--------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
