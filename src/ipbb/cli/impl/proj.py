from __future__ import print_function

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from ...tools.common import SmartOpen
from .. import kProjAreaFile, kProjDir, ProjectInfo
from ..utils import DirSentry, raiseError, validateComponent
from ...depparser.Pathmaker import Pathmaker

from os.path import join, split, exists, splitext, relpath, isdir
from click import echo, style, secho


# ------------------------------------------------------------------------------
# TODO: move the list of supported products somewhere else
def create(env, kind, projname, component, topdep):
    '''Creates a new area of name PROJNAME of kind KIND

      KIND: Area kind, choices: vivado, sim

      PROJNAME: Name of the new project area

      COMPONENT: Component <package:component> contaning the top-level
    '''
    # ------------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raiseError("Build area root directory not found")
        # raise click.ClickException('Build area root directory not found')
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    lProjAreaPath = join(env.work.path, kProjDir, projname)
    if exists(lProjAreaPath):
        raiseError("Directory {} already exists".format(lProjAreaPath))
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------

    lPathmaker = Pathmaker(env.srcdir, 0)
    lTopPackage, lTopComponent = component

    if lTopPackage not in env.sources:
        secho('Top-level package {} not found'.format(lTopPackage), fg='red')
        echo('Available packages:')
        for lPkg in env.sources:
            echo(' - ' + lPkg)

        raiseError("Top-level package {} not found".format(lTopPackage))
        # raise click.ClickException('Top-level package %s not found' % lTopPackage)

    if not exists(lPathmaker.getPath(lTopPackage, lTopComponent)):
        lTopPkgPath = lPathmaker.getPath(lTopPackage)
        secho(
            'Top-level component {}:{} not found'.format(lTopPackage, lTopComponent),
            fg='red',
        )
        echo('Available components')
        # When in Py3 https://docs.python.org/3/library/os.html#os.scandir
        for d in [
            join(lTopPkgPath, s)
            for s in os.listdir(lTopPkgPath)
            if isdir(join(lTopPkgPath, s))
        ]:
            echo(' - ' + d)

        raiseError(
            "Top-level component {}:{} not found".format(lTopPackage, lTopComponent)
        )

    lTopDepPath = lPathmaker.getPath(lTopPackage, lTopComponent, 'include', topdep)
    if not exists(lTopDepPath):
        import glob

        lTopDepDir = lPathmaker.getPath(lTopPackage, lTopComponent, 'include')
        lTopDepCandidates = [
            "'{}'".format(relpath(p, lTopDepDir))
            for p in glob.glob(join(lTopDepDir, '*.dep'))
        ]
        secho('Top-level dep file {} not found'.format(lTopDepPath), fg='red')
        echo('Suggestions (*.dep):')
        for lC in lTopDepCandidates:
            echo(' - ' + lC)

        raiseError("Top-level dependency file {} not found".format(lTopDepPath))
        # raise click.ClickException('Top-level dependency file %s not found' % lTopDepPath)
    # ------------------------------------------------------------------------------

    # Build source code directory
    os.makedirs(lProjAreaPath)

    pi = ProjectInfo()
    pi.path = lProjAreaPath
    pi.settings = {
        'toolset': kind,
        'topPkg': lTopPackage,
        'topCmp': lTopComponent,
        'topDep': topdep,
        'name': projname,
    }
    pi.saveSettings()

    secho(
        '{} project area \'{}\' created'.format(kind.capitalize(), projname), fg='green'
    )


# ------------------------------------------------------------------------------


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


# ------------------------------------------------------------------------------
@click.pass_obj
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


# ------------------------------------------------------------------------------
