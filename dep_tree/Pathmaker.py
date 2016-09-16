from __future__ import print_function
import os

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class Pathmaker(object):
  
  fpaths = {"src": "firmware/hdl", "include": "firmware/cfg", "addrtab": "addr_table", "setup": "firmware/cfg"}
  fexts = {"src": "vhd", "include": "dep", "addrtab": "xml" } #, "setup": "tcl"}
  
  #--------------------------------------------------------------
  def __init__(self, root, top, mapfile, verbosity):
    self.root = root
    self.top = top
    self.verbosity = verbosity
    self.componentmap = None
    
    if self.verbosity > 2:
      print("+++ Pathmaker init", root, top, mapfile)
      
    if mapfile:
      self.componentmap = dict()
      with open(aFileName) as lFile:
        for lLine in lFile:
          lLine = lLine.strip()
          if lLine == "" or lLine[0] == "#": continue
          lTokenized = lLine.split()
          self.componentmap[ lTokenized[0] ] = lTokenized[1]
  #--------------------------------------------------------------
      
  #--------------------------------------------------------------
  def getcomppath(self, componentname):
    if componentname == "ipcore_dir":
      return "ipcore_dir"
    elif componentname == "top":
      return self.top
    if self.componentmap is None:
      return componentname
    else:
      return componentmap[componentname]
  #--------------------------------------------------------------
  
  #--------------------------------------------------------------
  def getdefname(self, kind, name):
    return "{0}.{1}".format( name , self.fexts[kind] )
  #--------------------------------------------------------------
  
  #--------------------------------------------------------------
  def getpath(self, comp, kind = None, name = None, defext = False, cd = None): #descend = None, subdir = None
    path = [ self.getcomppath(comp) ]
         
    if kind:
      path.append( self.fpaths[kind] )
    
    if cd:
      path.append( cd )
    
    if name: 
      if defext:
        path.append( self.getdefname(kind, name) )
      else:
        path.append( name )
    
    path2 = os.path.normpath( os.path.join( self.root , *path ) )
    
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
