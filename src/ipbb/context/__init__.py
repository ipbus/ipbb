
# Import click for ansi colors
import yaml
import cerberus

from .. import utils

from os import walk, getcwd
from os.path import join, split, exists, splitext, basename, dirname

from ..defaults import kWorkAreaFile, kProjAreaFile, kProjUserFile, kSourceDir, kProjDir, kRepoFile, kDeprecatesSetupFile
from ..console import cprint

from rich.panel import Panel
from rich.style import Style


# TODO:
# Look into schema yaml schema validation: i.e.
# https://github.com/Grokzen/pykwalify
# or
# https://docs.python-cerberus.org/en/stable/install.html

src_repo_schema = {
    'reset': {
        'type': 'list',
        'schema': {
            'type': 'string'
        }
    },
    'init': {
        'type': 'list',
        'schema': {
            'type': 'string'
        }
    },
    'deptree': {
        'type': 'dict'
    }
}

proj_settings_schema = {
    'name': {'type': 'string'},
    'toolset': {'type': 'string', 'allowed': ['vivado', 'vitis_hls', 'sim']},
    'topCmp': {'type': 'string'},
    'topDep': {'type': 'string'},
    'topPkg': {'type': 'string'},
}


# ------------------------------------------------------------------------------
class FolderInfo(object):
    '''Utility class, attributes holder'''
    pass


# ------------------------------------------------------------------------------
class SourceInfo(FolderInfo):
    """Helper Class to contain source repository settings"""
    def __init__(self, aName, aPath):
        super(SourceInfo, self).__init__()


        self._repo_settings = None

        self.name = aName
        self.path = aPath

    # ------------------------------------------------------------------------------
    @property
    def deprecated_setup_settings_path(self):
        return join(self.path, kDeprecatesSetupFile)

    # ------------------------------------------------------------------------------
    @property
    def repo_settings_path(self):
        if self.path is None:
            return ""
        return join(self.path, kRepoFile)


    # ------------------------------------------------------------------------------
    @property
    def repo_settings(self):
        if self._repo_settings is None:
            self.load_repo_settings()

        return self._repo_settings

    # ------------------------------------------------------------------------------
    def load_repo_settings(self):

        repo_settings_path = self.repo_settings_path

        # Check if repo_setting exists
        if not exists(repo_settings_path):
            # Check if the old setup file exists
            repo_settings_path = self.deprecated_setup_settings_path
            if exists(repo_settings_path):
                cprint(Panel(f"\n[yellow]{self.name}: '{kDeprecatesSetupFile}' is deprecated. Use {kRepoFile} instead[/yellow]\n", title="[yellow]DEPRECATION WARNING[/yellow]", style=Style(color="yellow", italic=True)))
            else:
                self._repo_settings = {}
                return

        with open(self.repo_settings_path, 'r') as f:
            self._repo_settings = yaml.safe_load(f)

        self.validate_repo_settings()

    # ------------------------------------------------------------------------------
    def validate_repo_settings(self):

        ss = self.repo_settings
        if not ss:
            return

        vtor = cerberus.Validator(src_repo_schema)

        val = vtor.validate(ss)
        if not val:
            cprint(vtor.errors)


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
        self.load_settings()
        self.load_user_settings()

    # ------------------------------------------------------------------------------
    def load_settings(self):
        if not exists(self.filepath):
            return

        self.name = basename(self.path)

        # Import project settings
        with open(self.filepath, 'r') as f:
            self.settings = yaml.safe_load(f)

    # ------------------------------------------------------------------------------
    def load_user_settings(self):
        if not exists(self.userfilepath):
            return

        with open(self.userfilepath, 'r') as f:
            self.usersettings = yaml.safe_load(f)

    # ------------------------------------------------------------------------------
    def save_settings(self, jsonindent=2):
        if not self.settings:
            return
        with open(self.filepath, 'w') as f:
            yaml.safe_dump(self.settings, f, indent=jsonindent, default_flow_style=False)

    # ------------------------------------------------------------------------------
    def save_user_settings(self, jsonindent=2):
        if not self.usersettings:
            return
        with open(self.userfilepath, 'w') as f:
            yaml.safe_dump(self.usersettings, f, indent=jsonindent, default_flow_style=False)

    # ------------------------------------------------------------------------------
    def validate_settings(self):
        import cerberus
        v = cerberus.Validator()

        x = v.validate(self.settings, proj_settings_schema)
        print('Proj Doc Validated', x)
        print(v.errors)

    # ------------------------------------------------------------------------------
    def validateUserSettings(self):
        pass



# ------------------------------------------------------------------------------
class Context(object):
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
        self._dep_parser = None

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
        lWorkAreaPath = utils.findFileDirInParents(kWorkAreaFile, self._wd)

        # Stop here is no signature is found
        if not lWorkAreaPath:
            return

        self.work.path, self.work.cfgFile = lWorkAreaPath, kWorkAreaFile

        # -----------------------------
        self.pathMaker = Pathmaker(self.srcdir, self._verbosity)

        # -----------------------------
        lProjAreaPath = utils.findFileDirInParents(kProjAreaFile, self._wd)
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
    parser: {_dep_parser}
    }})'''.format(
                **(self.__dict__)
            )
        )

    # -----------------------------------------------------------------------------
    @property
    def depParser(self):
        if self._dep_parser is None:

            from ..depparser import DepFileParser

            # Collect package-level deptree defaults
            deptree_defaults = { k:v.repo_settings.get('deptree', {}) for k,v in self.sources_info.items() }
            self._dep_parser = DepFileParser(
                self.currentproj.settings['toolset'],
                self.pathMaker,
                deptree_defaults,
                self._verbosity,
            )

            try:
                self._dep_parser.parse( self.currentproj.settings['topPkg'], self.currentproj.settings['topCmp'], self.currentproj.settings['topDep'],)
            except OSError:
                pass

            if self._dep_parser.errors:
                cprint('WARNING: dep parsing errors detected', style='yellow')
        return self._dep_parser


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
    @property
    def sources_info(self):
        return {src: SourceInfo(src, join(self.srcdir, src)) for src in self.sources }

# -----------------------------------------------------------------------------
