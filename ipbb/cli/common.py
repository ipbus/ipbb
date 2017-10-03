from __future__ import print_function
# ------------------------------------------------------------------------------
import os
from click import secho, confirm, get_current_context

# ------------------------------------------------------------------------------
class DirSentry:
    def __init__(self, aDir):
        self.dir = aDir

    def __enter__(self):
        if not os.path.exists(self.dir):
            raise RuntimeError('Directory ' + self.dir + ' does not exist')

        self._lOldDir = os.path.realpath(os.getcwd())
        # print self._lOldDir
        os.chdir(self.dir)
        return self

    def __exit__(self, type, value, traceback):
        os.chdir(self._lOldDir)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def findFileInParents(aAreaFileName):
    lPath = os.getcwd()

    while lPath is not '/':
        lBuildFile = os.path.join(lPath, aAreaFileName)
        if os.path.exists(lBuildFile):
            return lBuildFile
        lPath, _ = os.path.split(lPath)

    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def ensureNoMissingFiles(aCurrentProj, aDepFileParser):

    if not aDepFileParser.NotFound:
        return

    lRootName = get_current_context().find_root().info_name
    secho("ERROR: Project '{}' contains unresolved dependencies: {} missing file{}.\n       Run '{} dep report' for details".format(
        aCurrentProj,
        len(aDepFileParser.NotFound),
        ("" if len(aDepFileParser.NotFound) == 1 else "s"),
        lRootName,
    ), fg='red')
    confirm("Do you want to continue anyway?", abort=True)
# ------------------------------------------------------------------------------
