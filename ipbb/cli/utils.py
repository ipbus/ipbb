from __future__ import print_function
# ------------------------------------------------------------------------------

import os

from click import echo, secho, style, confirm, get_current_context

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

    if not aDepFileParser.missing:
        return

    lRootName = get_current_context().find_root().info_name
    secho("ERROR: Project '{}' contains missing dependencies: {} missing file{}.\n       Run '{} dep report' for details".format(
        aCurrentProj,
        len(aDepFileParser.missing),
        ("" if len(aDepFileParser.missing) == 1 else "s"),
        lRootName,
    ), fg='red')
    confirm("Do you want to continue anyway?", abort=True)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def echoVivadoConsoleError( aExc ):
    echo(
        style("Vivado error/critical warnings detected\n", fg='red')+
        style("\n".join(aExc.errors), fg='red') + '\n' +
        style("\n".join(aExc.criticalWarns), fg='yellow') 
    )

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def validateComponent(ctx, param, value):
    lSeparators = value.count(':')
    # Validate the format
    if lSeparators != 1:
        raise click.BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

    return tuple(value.split(':'))
# ------------------------------------------------------------------------------
