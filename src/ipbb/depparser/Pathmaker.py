from __future__ import print_function, absolute_import
import os

# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


class Pathmaker(object):

    fpaths = {
        "src": "firmware/hdl",
        "include": "firmware/cfg",
        "addrtab": "addr_table",
        "setup": "firmware/cfg",
        "util": "firmware/cfg",
        "iprepo": "firmware/cgn",
    }
    fexts = {
        "src": "vhd",
        "include": "dep",
        "addrtab": "xml"
        # , "setup": "tcl"}
    }

    # --------------------------------------------------------------
    def __init__(self, rootdir, verbosity=0):
        self._rootdir = rootdir
        self._verbosity = verbosity

        if self._verbosity > 3:
            print("+++ Pathmaker init", rootdir)
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def getPackagePath(self, aPackage):
        return os.path.normpath(os.path.join(self._rootdir, aPackage))
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def packageExists(self, aPackage):
        return os.path.exists(self.getPackagePath(aPackage))
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def getPath(self, package, component=None, command=None, name=None, cd=None):

        # path = [package, component]
        path = [package]

        if component:
            path.append(component)

        if command:
            path.append(self.fpaths[command])

        if cd:
            path.append(cd)

        if name:
            path.append(name)

        lPath = os.path.normpath(os.path.join(self._rootdir, *path))

        if self._verbosity > 2:
            print('+++ Pathmaker', package, component, command, name, cd)
        return lPath
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def getDefName(self, command, name):
        return "{0}.{1}".format(name, self.fexts[command])
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def glob(self, package, component, command, fileexpr, cd=None):
        """
        Returns the complete path expression as well as the list of files matches
        """
        import glob

        lPathExpr = self.getPath(package, component, command, fileexpr, cd=cd)
        lKindPath = self.getPath(package, component, command, cd=cd)

        # Expand the expression
        lFilePaths = glob.glob(lPathExpr)

        # Calculate the relative path and pair it up with the absolute path
        lFileList = [(os.path.relpath(lPath2, lKindPath), lPath2)
                     for lPath2 in lFilePaths]

        return lPathExpr, lFileList
    # --------------------------------------------------------------
