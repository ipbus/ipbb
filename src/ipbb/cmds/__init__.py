
# Import click for ansi colors
import yaml

from . import _utils

from os import walk, getcwd
from os.path import join, split, exists, splitext, basename, dirname

from ..defaults import kWorkAreaFile, kProjAreaFile, kProjUserFile, kSourceDir, kProjDir
from ..console import cprint


# ------------------------------------------------------------------------------
class FolderInfo(object):
    '''Utility class, attributes holder'''

    pass


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class ProjectInfo(FolderInfo):
    '''
    Helper class to contain project information and configuration parameters
    Provides methods to load/save configuration fragments to file.
    '''

    # ------------------------------------------------------------------------------
    def __init__(self, aPath=None):
        self.name = None
        self.path = None
        self.settings = {}
        self.usersettings = {}

        if aPath is None:
            return

        self.load(aPath)

    # ------------------------------------------------------------------------------
    @property
    def filepath(self):
        if self.path is None:
            return ""
        return join(self.path, kProjAreaFile)

    # ------------------------------------------------------------------------------
    @property
    def userfilepath(self):
        if self.path is None:
            return ""
        return join(self.path, kProjUserFile)

    # ------------------------------------------------------------------------------
    def load(self, aPath):
        self.path = aPath

        if not exists(self.filepath):
            raise RuntimeError(
                "Missing project area definition at {}".format(self.filepath)
            )

        self.name = basename(self.path)
        self.loadSettings()
        self.loadUserSettings()

    # ------------------------------------------------------------------------------
    def loadSettings(self):
        # lProjAreaFilePath = join(self.path, kProjAreaFile)
        if not exists(self.filepath):
            return

        # self.path, self.file = split(lProjAreaFilePath)
        self.name = basename(self.path)

        # Import project settings
        with open(self.filepath, 'r') as f:
            self.settings = yaml.safe_load(f)

    # ------------------------------------------------------------------------------
    def loadUserSettings(self):
        if not exists(self.userfilepath):
            return

        with open(self.userfilepath, 'r') as f:
            self.usersettings = yaml.safe_load(f)

    # ------------------------------------------------------------------------------
    def saveSettings(self, jsonindent=2):
        if not self.settings:
            return
        with open(self.filepath, 'w') as f:
            yaml.safe_dump(self.settings, f, indent=jsonindent, default_flow_style=False)

    # ------------------------------------------------------------------------------
    def saveUserSettings(self, jsonindent=2):
        if not self.usersettings:
            return
        with open(self.userfilepath, 'w') as f:
            yaml.safe_dump(self.usersettings, f, indent=jsonindent, default_flow_style=False)


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class Environment(object):
    """docstring for Environment"""

    _verbosity = 0
    printExceptionStack = False

    # ----------------------------------------------------------------------------
    def __init__(self, wd=getcwd()):
        super().__init__()

        self._wd = wd
        self._autodetect()


    # ------------------------------------------------------------------------------
    def _clear(self):
        self._depParser = None

        self.work = FolderInfo()
        self.work.path = None
        self.work.cfgFile = None

        self.currentproj = ProjectInfo()

        self.pathMaker = None

    # ----------------------------------------------------------------------------
    def _autodetect(self):
        from ..depparser import Pathmaker

        self._clear()

        # -----------------------------
        lWorkAreaPath = _utils.findFileDirInParents(kWorkAreaFile, self._wd)

        # Stop here is no signature is found
        if not lWorkAreaPath:
            return

        self.work.path, self.work.cfgFile = lWorkAreaPath, kWorkAreaFile
        self.pathMaker = Pathmaker(self.srcdir, self._verbosity)
        # -----------------------------

        # -----------------------------
        lProjAreaPath = _utils.findFileDirInParents(kProjAreaFile, self._wd)
        if not lProjAreaPath:
            return

        self.currentproj.load(lProjAreaPath)

    # -----------------------------------------------------------------------------
    def __str__(self):
        return (
            self.__repr__()
            + '''({{
    work area path: {work.path}
    project area: {currentproj.name}
    project configuration: {currentproj.settings}
    user settings: {currentproj.usersettings}
    pathMaker: {pathMaker}
    parser: {_depParser}
    }})'''.format(
                **(self.__dict__)
            )
        )

    # -----------------------------------------------------------------------------
    @property
    def depParser(self):
        if self._depParser is None:

            from ..depparser import DepFileParser

            self._depParser = DepFileParser(
                self.currentproj.settings['toolset'],
                self.pathMaker,
                aVerbosity=self._verbosity,
            )

            try:
                self._depParser.parse( self.currentproj.settings['topPkg'], self.currentproj.settings['topCmp'], self.currentproj.settings['topDep'],)
            except OSError:
                pass

            if self._depParser.errors:
                cprint('WARNING: dep parsing errors detected', style='yellow')
        return self._depParser


    # -----------------------------------------------------------------------------
    @property
    def srcdir(self):
        return join(self.work.path, kSourceDir) if self.work.path is not None else None

    # -----------------------------------------------------------------------------
    @property
    def projdir(self):
        return join(self.work.path, kProjDir) if self.work.path is not None else None

    # -----------------------------------------------------------------------------
    @property
    def sources(self):
        return next(walk(self.srcdir))[1]

    # -----------------------------------------------------------------------------
    @property
    def projects(self):
        return [
            lProj
            for lProj in next(walk(self.projdir))[1]
            if exists(join(self.projdir, lProj, kProjAreaFile))
        ]

    # -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
