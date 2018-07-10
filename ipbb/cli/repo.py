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
from .utils import DirSentry, findFileInParents
from urlparse import urlparse
from distutils.dir_util import mkpath
from texttable import Texttable


# ------------------------------------------------------------------------------
@click.command('init', short_help="Initialise a new working area.")
@click.argument('workarea')
@click.pass_obj
def init(env, workarea):
    '''Initialise a new firmware development area'''

    secho('Setting up new firmware work area \'' + workarea + '\'', fg='green')

    if env.work.path is not None:
        raise click.ClickException(
            'Cannot create a new work area inside an existing one %s' % env.work.path)

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
@click.group('add', short_help="Add source packages.")
@click.pass_obj
def add(env):
    '''Add a new package to the source area'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@add.command('git', short_help="Add new source package from a git repository")
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
    lRepoLocalPath = join(env.work.path, kSourceDir, lRepoName)

    # Check for #    import pdb; pdb.set_trace()
#    if exists(lRepoLocalPath):
#        raise click.ClickException(
#            'Repository already exists \'%s\'' % lRepoLocalPath
#            )

    if branch is not None:
        lLsRemote = sh.git('ls-remote', '-h','-t', repo, branch)
        lRemoteRefs = [ line.strip().split('\t') for line in lLsRemote.split('\n') if line]


        # Handle unexpected cases
        # No references
        if not lRemoteRefs:
            raise click.ClickException(
                'No references matching \'{}\' found'.format(branch)
                )
        # Multiple references
        elif len(lRemoteRefs) > 1:
            echo(lRemoteRefs)
            raise click.ClickException(
                'Found {} references matching \'{}\''.format(len(lRemoteRefs), branch)
                )

        lRef, lRefName = lRemoteRefs[0]

        # It's either a branch (i.e. head)
        if lRefName.startswith('refs/heads/'):
            lRefKind = 'branch'
        # Or a tag
        elif lRefName.startswith('refs/tags/'):
            lRefKind = 'tag'
        # Or something alien
        else:
            raise click.ClickException(
                '{} is neither a branch nor a tag: {}'.format(len(branch), lRefName)
                )

        # All good, go ahead with cloning
        echo("{} {} resolved as reference {}".format(lRefKind.capitalize(), style(branch, fg='blue'), lRefName))

    lArgs = ['clone', repo]

    if dest is not None:
        lArgs += [dest]

    sh.git(*lArgs, _out=sys.stdout, _cwd=env.srcdir)

    if branch is not None:

        echo('Checking out branch/tag ' + style(branch, fg='blue'))
        sh.git('checkout', branch, '-q', _out=sys.stdout, _cwd=lRepoLocalPath)

    secho('Repository \'{}\' successfully cloned to:\n  {}'.format(lRepoName, join(env.srcdir,lRepoName)), fg='green')
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@add.command('svn', short_help="Add new source package from a svn repository.")
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

    lRepoLocalPath = join(env.srcdir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException(
            'Repository already exists \'%s\'' % lRepoLocalPath)
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    if not sparse:
        lArgs = ['checkout', '-q', repo]

        # Append destination directory if defined
        if dest is not None:
            lArgs.append(dest)

        if rev is not None:
            lArgs += ['-r', str(rev)]

        # Do the checkout
        lCmd = ['svn'] + lArgs
        echo('Executing ' + style(' '.join(lCmd), fg='blue'))
        if not dryrun:
            sh.svn(*lArgs, _out=sys.stdout, _cwd=env.srcdir)
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
            sh.svn(*lArgs, _out=sys.stdout, _cwd=env.srcdir)
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
@add.command('tar', short_help="Add new source package from tarball.")
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
    lRepoLocalPath = join(env.work.path, kSourceDir, lRepoName)

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
@click.group('srcs', short_help="Utility commands to handle source packagess.")
@click.pass_obj
def srcs(env):
    pass
# ------------------------------------------------------------------------------


@srcs.command('run', short_help="Run stuff")
@click.option('-p', '--pkg', default=None)
@click.argument('cmd', nargs=1)
@click.argument('args', nargs=-1)
@click.pass_obj
def run(env, pkg, cmd, args):

    if pkg:
        if pkg not in env.sources:
            secho  ( "ERROR: '{}' package not known.\nKnown packages:\n{}".format(pkg, '\n'.join(( ' * '+s for s in env.sources))), fg='red' )
            raise click.ClickException("Command failed")
        wd = join(env.srcdir, pkg)
    else:
        wd = env.srcdir

    try:
        lCmd = sh.Command(cmd)
    except sh.CommandNotFound as lExc:
        secho("ERROR: Command '{}' not found in path".format(cmd), fg='red')
        raise click.ClickException("Command aborted")


    try:
        lCmd(*args, _cwd=wd, _out=sys.stdout, _err=sys.stderr)
    except sh.ErrorReturnCode as lExc:
        raise click.ClickException("Command '{}' failed with error code {}".format(lExc.full_cmd, lExc.exit_code))


# ------------------------------------------------------------------------------
@srcs.command('status', short_help="Summary of the status of source packages.")
@click.pass_obj
def status(env):

    if not env.work.path:
        secho  ( 'ERROR: No ipbb work area detected', fg='red' )
        return

    secho ( "Packages", fg='blue' )
    lSrcs = env.sources
    if not lSrcs:
        return

    lSrcTable = Texttable(max_width=0)
    lSrcTable.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSrcTable.set_chars(['-', '|', '+', '-'])
    lSrcTable.header(['name', 'kind', 'version'])
    for lSrc in lSrcs:
        lSrcDir = join(env.srcdir, lSrc)

        lKind, lHEADId = "unknown", None

        # Check if a git repository
        if exists(join( lSrcDir, '.git')):
            with DirSentry(lSrcDir) as _:

                lKind = 'git'
                try:
                    sh.git('rev-parse','--git-dir')
                except sh.ErrorReturnCode_128:
                    lKind += ' (broken)'
                    lHEADId = '(unknown)'             


                if lKind == 'git':
                    try:
                        lBranch = '/'.join(sh.git('symbolic-ref', 'HEAD').split('/')[2:]).strip()
                    except sh.ErrorReturnCode_128:
                        lBranch = None
                            
                    try: 
                        lTag = sh.git('describe', '--tags', '--exact-match', 'HEAD').strip()
                    except sh.ErrorReturnCode_128:
                        lTag = None

                    if lTag is not None:
                        lHEADId = lTag
                    elif lBranch is not None:
                        lHEADId = lBranch
                    else:
                        lHEADId = sh.git('rev-parse', '--short', 'HEAD').strip()+'...'

                    try:
                        sh.git('diff', '--no-ext-diff', '--quiet').strip()
                    except sh.ErrorReturnCode_1:
                        lHEADId += '*'

                    try:
                        sh.git('diff', '--no-ext-diff', '--cached', '--quiet').strip()
                    except sh.ErrorReturnCode_1:
                        lHEADId += '+'
        elif exists(join( lSrcDir, '.svn')):
            with DirSentry(lSrcDir) as _:
                lKind = 'svn'

                lSVNInfoRaw = sh.svn('info')

                lSVNInfo = { lEntry[0]:lEntry[1].strip() for lEntry in ( lLine.split(':',1) for lLine in lSVNInfoRaw.split('\n') if lLine )}

                lHEADId = lSVNInfo['URL'].replace( lSVNInfo['Repository Root']+'/', '' )

                lSVNStatus = sh.svn('status','-q')
                if len(lSVNStatus):
                    lHEADId += '*'

        lSrcTable.add_row([lSrc, lKind, lHEADId])
    echo  ( lSrcTable.draw() )
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@srcs.command('find', short_help="Find src files.")
@click.pass_obj
def find(env):
    sh.find(env.srcdir,'-name', '*.vhd', _out=sys.stdout)
