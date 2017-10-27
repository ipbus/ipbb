from __future__ import print_function

# Modules
import click
import os
import subprocess
import sh
import sys

# Elements
from click import echo, style, secho
from os.path import join, split, exists, splitext, dirname, basename, abspath

from . import kSourceDir, kProjDir, kWorkAreaCfgFile
from .common import DirSentry, findFileInParents
from urlparse import urlparse
from distutils.dir_util import mkpath
from texttable import Texttable


# ------------------------------------------------------------------------------
@click.command()
@click.argument('workarea')
@click.pass_obj
def init(env, workarea):
    '''Initialise a new firmware development area'''

    secho('Setting up new firmware work area \'' + workarea + '\'', fg='green')

    if env.workPath is not None:
        raise click.ClickException(
            'Cannot create a new work area inside an existing one %s' % env.workPath)

    if exists(workarea):
        raise click.ClickException(
            'Directory \'%s\' already exists' % workarea)

    # Build source code directory
    mkpath(join(workarea, kSourceDir))
    mkpath(join(workarea, kProjDir))

    with open(join(workarea, kWorkAreaCfgFile), 'w') as lSignature:
        lSignature.write('\n')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.group()
@click.pass_obj
def add(env):
    '''Add a new package to the source area'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.workPath is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@add.command()
@click.argument('repo')
@click.option('-b', '--branch', default=None, help='Git branch or tag to clone')
@click.option('-d', '--dest', default=None, help="Destination directory")
@click.pass_obj
def git(env, repo, branch, dest):
    '''Add a git repository to the source area'''

    echo('Adding git repository ' + style(repo, fg='blue'))

    # Ensure that the destination direcotry doesn't exist
    # Maybe not necessary

    lUrl = urlparse(repo)
    # Strip '.git' at the end
    lRepoName = splitext(basename(lUrl.path))[0] if dest is None else dest
    lRepoLocalPath = join(env.workPath, kSourceDir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException(
            'Repository already exists \'%s\'' % lRepoLocalPath)

    lArgs = ['clone', repo]

    if dest is not None:
        lArgs += [dest]

    sh.git(*lArgs, _out=sys.stdout, _cwd=env.src)

    if branch is not None:
        echo('Checking out branch/tag ' + style(branch, fg='blue'))
        sh.git('checkout', branch, '-q', _out=sys.stdout, _cwd=lRepoLocalPath)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@add.command()
@click.argument('repo')
@click.option('-d', '--dest', default=None, help='Destination folder')
@click.option('-r', '--rev', type=click.INT, default=None, help='SVN revision')
@click.option('-n', '--dryrun', is_flag=True, help='Dry run')
@click.option('-s', '--sparse', default=None, multiple=True, help='List of subdirectories to check out.')
@click.pass_obj
def svn(env, repo, dest, rev, dryrun, sparse):
    '''Add a svn repository REPO to the source area'''

    lUrl = urlparse(repo)
    lRepoName = splitext(basename(lUrl.path))[0] if dest is None else dest
    # -------------------------------------------------------------------------
    # Stop if the target directory already exists
    echo('Adding svn repository ' + style(repo, fg='blue'))

    lRepoLocalPath = join(env.src, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException(
            'Repository already exists \'%s\'' % lRepoLocalPath)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not sparse:
        lArgs = ['checkout', repo]

        # Append destination directory if defined
        if dest is not None:
            lArgs.append(dest)

        if rev is not None:
            lArgs += ['-r', str(rev)]

        # Do the checkout
        lCmd = ['svn'] + lArgs
        echo('Executing ' + style(' '.join(lCmd), fg='blue'))
        if not dryrun:
            sh.svn(*lArgs, _out=sys.stdout, _cwd=env.src)
    else:
        echo ('Sparse checkout mode: ' + style(' '.join(sparse), fg='blue'))
        # ----------------------------------------------------------------------
        # Checkout an empty base folder
        lArgs = ['checkout', '--depth=empty', repo]

        # Append destination directory if defined
        if dest is not None:
            lArgs.append(dest)

        if rev is not None:
            lArgs += ['-r', str(rev)]

        lCmd = ['svn'] + lArgs
        echo('Executing ' + style(' '.join(lCmd), fg='blue'))
        if not dryrun:
            sh.svn(*lArgs, _out=sys.stdout, _cwd=env.src)
        # ----------------------------------------------------------------------
        lArgs = ['update']
        lCmd = ['svn'] + lArgs
        for lPath in sparse:
            lTokens = [lToken for lToken in lPath.split('/') if lToken]

            lPartials = ['/'.join(lTokens[:i + 1])
                         for i, _ in enumerate(lTokens)]

            # Recursively check out intermediate, empty folders
            for lPartial in lPartials:
                lArgs = ['up', '--depth=empty', lPartial]
                echo('Executing ' + style(' '.join(['svn'] + lArgs), fg='blue'))
                if not dryrun:
                    sh.svn(*lArgs, _out=sys.stdout, _cwd=lRepoLocalPath)

            # Finally check out the target
            lArgs = ['up', '--set-depth=infinity', lPath]
            echo('Executing ' + style(' '.join(['svn'] + lArgs), fg='blue'))
            if not dryrun:
                sh.svn(*lArgs, _out=sys.stdout, _cwd=lRepoLocalPath)
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@add.command()
@click.argument('repo')
@click.option('-d', '--dest', default=None, help='Destination folder')
@click.option('-s', '--strip', type=int, default=None, help='Strip <n> level of directories when unpacking.')
@click.pass_obj
def tar(env, repo, dest, strip):
    '''Add a tarball-ed package to the source area'''

    click.secho("Warning: Command 'untar' is still experimental", fg='yellow')
    lProtocols = ['file', 'http', 'https']
    lExtensions = ['.tar', '.tar.gz', '.tgz']

    # -------------------------------------------------------------------------
    # Carefully parse the repository uri
    lUrl = urlparse(repo)

    # Normalize the scheme name
    lUrlScheme = lUrl.scheme if lUrl.scheme else 'file'

    # And check if it is a known protocol
    if lUrl.scheme not in lProtocols:
        raise click.ClickException(
            "Protocol '" + lUrl.scheme +
            "'' not supported. Available protocols " +
            ", ".join(["'" + lP + "'" for lP in lProtocols])
        )

    # Normalize the path as well
    lUrlPath = lUrl.path if lUrlScheme != 'file' else join(lUrl.netloc, lUrl.path)

    if not lUrlPath:
        raise click.ClickException('Malformed url: ' + lUrl)

    lMatches = filter(lambda lOpt: lUrlPath.endswith(lOpt), lExtensions)
    if not lMatches:
        raise click.ClickException('File format not supported. Supported formats :' + ' '.join(lExtensions))

    lRepoName = basename(lUrlPath).strip(lMatches[0]) if dest is None else dest
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Stop if the target directory already exists
    echo('Adding tarball ' + style(repo, fg='blue') + ' to ' + style(lRepoName, fg='blue'))
    lRepoLocalPath = join(env.workPath, kSourceDir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException(
            'Repository already exists \'%s\'' % lRepoLocalPath)
    # -------------------------------------------------------------------------

    mkpath(lRepoLocalPath)

    lOptArgs = [] if strip is None else ['--show-transformed', '--strip=' + str(strip)]

    # First case, local file
    if lUrlScheme in ['file']:
        lArgs = ['xvfz', abspath(lUrlPath)] + lOptArgs
        sh.tar(*lArgs, _out=sys.stdout, _cwd=lRepoLocalPath)

    # Second case, remote file
    else:
        lArgs = ['xvz'] + lOptArgs
        sh.tar(sh.curl('-L', repo), *lArgs, _out=sys.stdout, _cwd=lRepoLocalPath)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.command()
@click.pass_obj
def srcstat(env):

    if not env.workPath:
        secho  ( 'ERROR: No ipbb work area detected', fg='red' )
        return

    secho ( "Packages", fg='blue' )
    lSrcs = env.getSources()
    if not lSrcs:
        return

    lSrcTable = Texttable()
    lSrcTable.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSrcTable.set_chars(['-', '|', '+', '-'])
    lSrcTable.header(['name', 'kind', 'version'])
    for lSrc in lSrcs:
        lSrcDir = join(env.src, lSrc)

        lKind, lBranch = "unknown", None

        # Check if a git repository
        if exists(join( lSrcDir, '.git')):
            with DirSentry(lSrcDir) as _:
                lKind = 'git'
                lBranch = sh.git('symbolic-ref','--short', 'HEAD').strip()

        lSrcTable.add_row([lSrc, lKind, lBranch])
    echo  ( lSrcTable.draw() )

# ------------------------------------------------------------------------------

