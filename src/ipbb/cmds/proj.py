
# Modules
import click
import os
import subprocess


# Elements
from ..console import cprint, console
from ..utils import SmartOpen
from ..defaults import kProjAreaFile, kProjDir, kTopDep
from ..context import ProjectInfo
from ..utils import DirSentry, raiseError, validateComponent, findFirstParentDir
from ..depparser import dep_file_types, Pathmaker

from rich.table import Table
from os.path import join, split, exists, splitext, relpath, isdir, basename

# ------------------------------------------------------------------------------
def info(ictx):

    lHeader = ('name', 'toolset', 'topPkg', 'topCmp', 'topDep')
    lProjTable = Table(*lHeader, title="Projects", title_style='blue')

    for p in sorted(ictx.projects):
        lProjInfo = ProjectInfo(join(ictx.projdir, p))
        lProjTable.add_row(p, *(lProjInfo.settings[k] for k in lHeader[1:]) )

    cprint(lProjTable)


# ------------------------------------------------------------------------------
def create(ictx, toolset, projname, component, topdep):
    '''
    Creates a new area of name PROJNAME
    
    TOOLSET: Toolset used for the project areas, choices: vivado, sim
    
    PROJNAME: Name of the new project area
    
    COMPONENT: Component <package:component> contaning the top-level
    
    TOPDEP: Top dependency file.
    '''
    # ------------------------------------------------------------------------------
    # Must be in a build area
    if ictx.work.path is None:
        raiseError("Build area root directory not found")

    # ------------------------------------------------------------------------------
    lProjAreaPath = join(ictx.work.path, kProjDir, projname)
    if exists(lProjAreaPath):
        raiseError("Directory {} already exists".format(lProjAreaPath))

    # ------------------------------------------------------------------------------
    lPathmaker = Pathmaker(ictx.srcdir, 0)
    lTopPackage, lTopComponent = component

    if lTopPackage not in ictx.sources:
        cprint('Top-level package {} not found'.format(lTopPackage), style='red')
        cprint('Available packages:')
        for lPkg in ictx.sources:
            cprint(' - ' + lPkg)

        raiseError("Top-level package {} not found".format(lTopPackage))

    lTopComponentPath = lPathmaker.getPath(lTopPackage, lTopComponent)
    if not exists(lTopComponentPath):
        cprint(
            "Top-level component '{}:{}'' not found".format(lTopPackage, lTopComponent),
            style='red',
        )

        lParent = findFirstParentDir(lTopComponentPath, lPathmaker.getPath(lTopPackage))
        cprint('\nSuggestions (based on the first existing parent path)', style='cyan')
        # When in Py3 https://docs.python.org/3/library/os.html#os.scandir
        for d in [
            join(lParent, s)
            for s in os.listdir(lParent)
            if isdir(join(lParent, s))
        ]:
            cprint(' - ' + d)
        cprint()

        raise click.Abort()


    # ------------------------------------------------------------------------------
    # FIXME: This is just an initial implementation to prove it works.
    # What was "it"?
    # To be improved later.
    if topdep == '__auto__':
        lFilePaths, _ = lPathmaker.globall(
            lTopPackage, lTopComponent, 'include', 
            lPathmaker.getDefNames('include', kTopDep)
        )
        lTopExists = (len(lFilePaths) == 1)
        lTopDep = lFilePaths[0][0][0] if lTopExists else lPathmaker.getDefNames('include', kTopDep, mode='braces')
        lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', lTopDep)
    else:
        lTopDep = topdep
        lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', lTopDep)
        lTopExists = exists(lTopDepPath)

    # ------------------------------------------------------------------------------
    if not lTopExists:
        import glob
        cprint('Top-level dep file {} not found or not uniquely resolved'.format(lTopDepPath), style='red')

        lTopDepDir = lPathmaker.getPath(lTopPackage, lTopComponent, 'include')

        for ft in dep_file_types:
            lTopDepCandidates = [
                "'{}'".format(relpath(p, lTopDepDir))
                for p in glob.glob(join(lTopDepDir, '*' + ft))
            ]
            cprint('Suggestions (*{}):'.format(ft))
            for lC in lTopDepCandidates:
                cprint(' - ' + lC)

        raiseError("Top-level dependency file {} not found".format(lTopDepPath))

    # Build source code directory
    os.makedirs(lProjAreaPath)

    pi = ProjectInfo()
    pi.path = lProjAreaPath
    pi.settings = {
        'toolset': toolset.replace('-', '_'),
        'topPkg': lTopPackage,
        'topCmp': lTopComponent,
        'topDep': lTopDep,
        'name': projname,
    }
    pi.saveSettings()

    console.log(f"{toolset.capitalize()} project area '{projname}' created", style='green')


# ------------------------------------------------------------------------------
def ls(ictx):
    '''Lists all available project areas
    '''
    lProjects = ictx.projects
    print('Main work area:', ictx.work.path)
    print(
        'Projects areas:',
        ', '.join(
            [
                lProject + ('*' if lProject == ictx.currentproj.name else '')
                for lProject in lProjects
            ]
        ),
    )


# ------------------------------------------------------------------------------
def cd(ictx, projname, aVerbose):
    '''Changes current working directory (command line only)
    '''

    if projname[-1] == os.sep:
        projname = projname[:-1]

    lProjects = ictx.projects
    if projname not in lProjects:
        raise click.ClickException(
            'Requested work area not found. Available areas: %s' % ', '.join(lProjects)
        )

    # with DirSentry(join(ictx.projdir, projname)) as lSentry:
    #     ictx._autodetect()

    os.chdir(join(ictx.projdir, projname))
    ictx._wd = os.getcwd()
    ictx._autodetect()

    # if aVerbose:
    cprint(f"New current directory {os.getcwd()}")
    cprint(ictx.currentproj.name)


