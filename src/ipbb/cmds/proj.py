from __future__ import print_function, absolute_import

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

from os.path import join, split, exists, splitext, relpath, isdir
from click import echo, style, secho
from texttable import Texttable

# ------------------------------------------------------------------------------
def info(env):

    secho("Projects", fg='blue')

    lHeader = ('name', 'toolset', 'topPkg', 'topCmp', 'topDep')
    lProjTable = Texttable(120)
    lProjTable.set_deco(Texttable.HEADER | Texttable.BORDER)
    lProjTable.set_chars(['-', '|', '+', '-'])
    lProjTable.header(lHeader)

    for p in sorted(env.projects):
        lProjInfo = ProjectInfo(join(env.projdir, p))
        lProjTable.add_row([p] + [lProjInfo.settings[k] for k in lHeader[1:]] )

    echo(lProjTable.draw())


# ------------------------------------------------------------------------------
def create(env, toolset, projname, component, topdep):
    '''
    Creates a new area of name PROJNAME
    
    TOOLSET: Toolset used for the project areas, choices: vivado, sim
    
    PROJNAME: Name of the new project area
    
    COMPONENT: Component <package:component> contaning the top-level
    
    TOPDEP: Top dependency file.
    '''
    # ------------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raiseError("Build area root directory not found")

    # ------------------------------------------------------------------------------
    lProjAreaPath = join(env.work.path, kProjDir, projname)
    if exists(lProjAreaPath):
        raiseError("Directory {} already exists".format(lProjAreaPath))

    # ------------------------------------------------------------------------------
    lPathmaker = Pathmaker(env.srcdir, 0)
    lTopPackage, lTopComponent = component

    if lTopPackage not in env.sources:
        secho('Top-level package {} not found'.format(lTopPackage), fg='red')
        echo('Available packages:')
        for lPkg in env.sources:
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


    # FIXME: This is just an initial implementation to prove it works.
    # To be improved later.
    if topdep == '__auto__':
        lTopDefault = 'top'
        lFilePaths, _ = lPathmaker.globall(
            lTopPackage, lTopComponent, 'include', 
            lPathmaker.getDefNames('include', lTopDefault)
        )

        lTopExists = (len(lFilePaths) == 1)
        lTopDepPath = lFilePaths[0] if lTopExists else lPathmaker.getDefNames('include', lTopDefault, 'braces')
    else:
        lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', topdep)
        lTopExists = exists(lTopDepPath)

    # lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', topdep)
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
    # ------------------------------------------------------------------------------

    # Build source code directory
    os.makedirs(lProjAreaPath)

    pi = ProjectInfo()
    pi.path = lProjAreaPath
    pi.settings = {
        'toolset': toolset,
        'topPkg': lTopPackage,
        'topCmp': lTopComponent,
        'topDep': topdep,
        'name': projname,
    }
    pi.saveSettings()

    secho(
        '{} project area \'{}\' created'.format(toolset.capitalize(), projname), fg='green'
    )


# ------------------------------------------------------------------------------
def ls(env):
    '''Lists all available project areas
    '''
    lProjects = env.projects
    print('Main work area:', env.work.path)
    print(
        'Projects areas:',
        ', '.join(
            [
                lProject + ('*' if lProject == env.currentproj.name else '')
                for lProject in lProjects
            ]
        ),
    )


# ------------------------------------------------------------------------------
def cd(env, projname, aVerbose):
    '''Changes current working directory (command line only)
    '''

    if projname[-1] == os.sep:
        projname = projname[:-1]

    lProjects = env.projects
    if projname not in lProjects:
        raise click.ClickException(
            'Requested work area not found. Available areas: %s' % ', '.join(lProjects)
        )

    with DirSentry(join(env.projdir, projname)) as lSentry:
        env._autodetect()

    os.chdir(join(env.projdir, projname))
    if aVerbose:
        echo("New current directory %s" % os.getcwd())


