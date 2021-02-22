
# Modules
import click
import os
import ipbb
import subprocess


# Elements
from ..tools.common import SmartOpen
from ..defaults import kProjAreaFile, kProjDir
from . import ProjectInfo
from ._utils import DirSentry, raiseError, validateComponent, findFirstParentDir
from ..depparser import depfiletypes, Pathmaker

from os.path import join, split, exists, splitext, relpath, isdir, basename
from click import echo, style, secho
from texttable import Texttable

# ------------------------------------------------------------------------------
def info(ictx):

    secho("Projects", fg='blue')

    lHeader = ('name', 'toolset', 'topPkg', 'topCmp', 'topDep')
    lProjTable = Texttable(120)
    lProjTable.set_deco(Texttable.HEADER | Texttable.BORDER)
    lProjTable.set_chars(['-', '|', '+', '-'])
    lProjTable.header(lHeader)

    for p in sorted(ictx.projects):
        lProjInfo = ProjectInfo(join(ictx.projdir, p))
        lProjTable.add_row([p] + [lProjInfo.settings[k] for k in lHeader[1:]] )

    echo(lProjTable.draw())


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
        secho('Top-level package {} not found'.format(lTopPackage), fg='red')
        echo('Available packages:')
        for lPkg in ictx.sources:
            echo(' - ' + lPkg)

        raiseError("Top-level package {} not found".format(lTopPackage))

    lTopComponentPath = lPathmaker.getPath(lTopPackage, lTopComponent)
    if not exists(lTopComponentPath):
        secho(
            "Top-level component '{}:{}'' not found".format(lTopPackage, lTopComponent),
            fg='red',
        )

        lParent = findFirstParentDir(lTopComponentPath, lPathmaker.getPath(lTopPackage))
        secho('\nSuggestions (based on the first existing parent path)', fg='cyan')
        # When in Py3 https://docs.python.org/3/library/os.html#os.scandir
        for d in [
            join(lParent, s)
            for s in os.listdir(lParent)
            if isdir(join(lParent, s))
        ]:
            echo(' - ' + d)
        echo()

        raise click.Abort()


    # ------------------------------------------------------------------------------
    # FIXME: This is just an initial implementation to prove it works.
    # To be improved later.
    if topdep == '__auto__':
        lTopDefault = 'top'
        lFilePaths, _ = lPathmaker.globall(
            lTopPackage, lTopComponent, 'include', 
            lPathmaker.getDefNames('include', lTopDefault)
        )
        lTopExists = (len(lFilePaths) == 1)
        lTopDep = lFilePaths[0][0][0] if lTopExists else lPathmaker.getDefNames('include', lTopDefault, 'braces')
        lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', lTopDep)
    else:
        lTopDep = topdep
        lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', lTopDep)
        lTopExists = exists(lTopDepPath)

    # ------------------------------------------------------------------------------
    if not lTopExists:
        import glob
        secho('Top-level dep file {} not found or not uniquely resolved'.format(lTopDepPath), fg='red')

        lTopDepDir = lPathmaker.getPath(lTopPackage, lTopComponent, 'include')

        for ft in depfiletypes:
            lTopDepCandidates = [
                "'{}'".format(relpath(p, lTopDepDir))
                for p in glob.glob(join(lTopDepDir, '*' + ft))
            ]
            echo('Suggestions (*{}):'.format(ft))
            for lC in lTopDepCandidates:
                echo(' - ' + lC)

        raiseError("Top-level dependency file {} not found".format(lTopDepPath))

    # Build source code directory
    os.makedirs(lProjAreaPath)

    pi = ProjectInfo()
    pi.path = lProjAreaPath
    pi.settings = {
        'toolset': toolset,
        'topPkg': lTopPackage,
        'topCmp': lTopComponent,
        'topDep': lTopDep,
        'name': projname,
    }
    pi.saveSettings()

    secho(
        '{} project area \'{}\' created'.format(toolset.capitalize(), projname), fg='green'
    )


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

    with DirSentry(join(ictx.projdir, projname)) as lSentry:
        ictx._autodetect()

    os.chdir(join(ictx.projdir, projname))
    if aVerbose:
        echo("New current directory %s" % os.getcwd())


