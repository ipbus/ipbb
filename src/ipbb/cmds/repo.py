from __future__ import print_function, absolute_import
from future.standard_library import install_aliases
install_aliases()
# ------------------------------------------------------------------------------

# Modules
import click
import os
import subprocess
import sh
import sys
import yaml

# Elements
from click import echo, style, secho
from os.path import join, split, exists, splitext, dirname, basename, abspath

from ..defaults import kSourceDir, kProjDir, kWorkAreaFile, kRepoSetupFile
from ._utils import DirSentry, findFileInParents, raiseError
from ..depparser import Pathmaker
from ..tools.common import mkdir
from urllib.parse import urlparse
from distutils.dir_util import mkpath
from texttable import Texttable


# ------------------------------------------------------------------------------
def init(env, workarea):
    '''Initialise a new firmware development area'''

    secho('Setting up new firmware work area \'' + workarea + '\'', fg='green')

    if env.work.path is not None:
        raise click.ClickException(
            'Cannot create a new work area inside an existing one %s' % env.work.path
        )

    if exists(workarea) and os.listdir(workarea):
        raise click.ClickException('Directory \'%s\' already exists and it\'s not empty' % workarea)

    # Build source code directory
    mkpath(join(workarea, kSourceDir))
    mkpath(join(workarea, kProjDir))

    with open(join(workarea, kWorkAreaFile), 'w') as lSignature:
        lSignature.write('\n')


# ------------------------------------------------------------------------------
def add(env):
    '''Add a new package to the source area'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def _repoInit(env, dest):

    if dest not in env.sources:
        secho('Source package {} not found'.format(dest), fg='red')
        echo('Available repositories:')
        for lPkg in env.sources:
            echo(' - ' + lPkg)

        raiseError("Source package {} not found".format(dest))

    setupPath = join(env.srcdir, dest, kRepoSetupFile)
    if not exists(setupPath):
        secho('No repository setup file found in {}. Skipping'.format(dest), fg='blue')
        return
    secho('Setting up {}'.format(dest), fg='blue')

    setupCfg = None
    with open(setupPath, 'r') as f:
        setupCfg = yaml.safe_load(f)

    setupCfg = setupCfg.get('init', None)
    if setupCfg is None:
        echo("No init configuration file. Skipping.")
        return

    cmds = [ l.split() for l in setupCfg ]

    # ensure that all commands exist
    missingCmds = [(i, cmd) for i, cmd in enumerate(cmds) if not sh.which(cmd[0])]
    if missingCmds:
        secho('Some setup commands have not been found', fg='red')
        for i, cmd in missingCmds:
            echo(' - {} (line {})'.format(cmd, i))

        raiseError("Setup commands not found".format(dest))

    with sh.pushd(join(env.srcdir, dest)):
        # TODO: add error handling
        # Show the list of commands
        # In green the commands executed successfully
        # In red the failed one
        # In white the remaining commands
        for cmd in cmds:
            secho('> '+' '.join(cmd), fg='cyan')
            sh.Command(cmd[0])(*cmd[1:], _out=sys.stdout)

# ------------------------------------------------------------------------------
def _repoReset(env, dest):

    if dest not in env.sources:
        secho('Source package {} not found'.format(dest), fg='red')
        echo('Available repositories:')
        for lPkg in env.sources:
            echo(' - ' + lPkg)

        raiseError("Source package {} not found".format(dest))

    setupPath = join(env.srcdir, dest, kRepoSetupFile)
    if not exists(setupPath):
        secho('No repository setup file found in {}. Skipping'.format(dest), fg='blue')
        return
    secho('Resetting up {}'.format(dest), fg='blue')

    setupCfg = None
    with open(setupPath, 'r') as f:
        setupCfg = yaml.safe_load(f)

    setupCfg = setupCfg.get('reset', None)
    if setupCfg is None:
        echo("No reset configuration file. Skipping.")
        return

    cmds = [ l.split() for l in setupCfg ]

    # ensure that all commands exist
    missingCmds = [(i, cmd) for i, cmd in enumerate(cmds) if not sh.which(cmd[0])]
    if missingCmds:
        secho('Some setup commands have not been found', fg='red')
        for i, cmd in missingCmds:
            echo(' - {} (line {})'.format(cmd, i))

        raiseError("Setup commands not found".format(dest))

    with sh.pushd(join(env.srcdir, dest)):
        # TODO: add error handling
        # Show the list of commands
        # In green the commands executed successfully
        # In red the failed one
        # In white the remaining commands
        for cmd in cmds:
            secho('> '+' '.join(cmd), fg='cyan')
            sh.Command(cmd[0])(*cmd[1:], _out=sys.stdout)

# ------------------------------------------------------------------------------
def git(env, repo, branch, dest):
    '''Add a git repository to the source area'''

    echo('Adding git repository ' + style(repo, fg='blue'))

    # Ensure that the destination direcotry doesn't exist
    # Maybe not necessary

    lUrl = urlparse(repo)
    # Strip '.git' at the end
    lRepoName = splitext(basename(lUrl.path))[0] if dest is None else dest
    lRepoLocalPath = join(env.work.path, kSourceDir, lRepoName)

    # Check for
    if exists(lRepoLocalPath):
        raise click.ClickException('Repository already exists \'%s\'' % lRepoLocalPath)

    if branch is not None:
        lLsRemote = sh.git('ls-remote', '-h', '-t', repo, branch)
        lRemoteRefs = [
            line.strip().split('\t') for line in lLsRemote.split('\n') if line
        ]

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
        echo(
            "{} {} resolved as reference {}".format(
                lRefKind.capitalize(), style(branch, fg='blue'), lRefName
            )
        )

    lArgs = ['clone', repo]

    if dest is not None:
        lArgs += [dest]

    sh.git(*lArgs, _out=sys.stdout, _cwd=env.srcdir)

    if branch is not None:

        echo('Checking out branch/tag ' + style(branch, fg='blue'))
        sh.git('checkout', branch, '-q', _out=sys.stdout, _cwd=lRepoLocalPath)

    secho(
        'Repository \'{}\' successfully cloned to:\n  {}'.format(
            lRepoName, join(env.srcdir, lRepoName)
        ),
        fg='green',
    )

    _repoInit(env, lRepoName)


# ------------------------------------------------------------------------------
def svn(env, repo, dest, rev, dryrun, sparse):
    '''Add a svn repository REPO to the source area'''

    lUrl = urlparse(repo)
    lRepoName = splitext(basename(lUrl.path))[0] if dest is None else dest
    # -------------------------------------------------------------------------
    # Stop if the target directory already exists
    echo('Adding svn repository ' + style(repo, fg='blue'))

    lRepoLocalPath = join(env.srcdir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException('Repository already exists \'%s\'' % lRepoLocalPath)
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
        echo('Sparse checkout mode: ' + style(' '.join(sparse), fg='blue'))
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

            lPartials = ['/'.join(lTokens[: i + 1]) for i, _ in enumerate(lTokens)]

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

    _repoInit(env, lRepoName)

    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
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
            "Protocol '"
            + lUrl.scheme
            + "'' not supported. Available protocols "
            + ", ".join(["'" + lP + "'" for lP in lProtocols])
        )

    # Normalize the path as well
    lUrlPath = lUrl.path if lUrlScheme != 'file' else join(lUrl.netloc, lUrl.path)

    if not lUrlPath:
        raise click.ClickException('Malformed url: ' + lUrl)

    lMatches = filter(lambda lOpt: lUrlPath.endswith(lOpt), lExtensions)
    if not lMatches:
        raise click.ClickException(
            'File format not supported. Supported formats :' + ' '.join(lExtensions)
        )

    lRepoName = basename(lUrlPath).strip(lMatches[0]) if dest is None else dest
    # -------------------------------------------------------------------------

    # -------------------------------------------------------------------------
    # Stop if the target directory already exists
    echo(
        'Adding tarball '
        + style(repo, fg='blue')
        + ' to '
        + style(lRepoName, fg='blue')
    )
    lRepoLocalPath = join(env.work.path, kSourceDir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException('Repository already exists \'%s\'' % lRepoLocalPath)
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

    _repoInit(env, lRepoName)


# ------------------------------------------------------------------------------
def symlink(env, path):

    lRepoName = basename(path)
    lRepoLocalPath = join(env.srcdir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException('Repository already exists \'%s\'' % lRepoLocalPath)

    echo(
        'Adding symlink '
        + style(abspath(path), fg='blue')
        + ' as '
        + style(lRepoName, fg='blue')
    )

    sh.ln('-s', abspath(path), _cwd=env.srcdir )


# ------------------------------------------------------------------------------
def srcs(env):
    pass


# ------------------------------------------------------------------------------
def info(env):

    if not env.work.path:
        secho('ERROR: No ipbb work area detected', fg='red')
        return

    echo()
    secho("Packages", fg='blue')
    lSrcs = env.sources
    if not lSrcs:
        return

    lSrcTable = Texttable(max_width=0)
    lSrcTable.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSrcTable.set_chars(['-', '|', '+', '-'])
    lSrcTable.header(['name', 'kind', 'version', 'hash'])
    for lSrc in lSrcs:
        lSrcDir = join(env.srcdir, lSrc)

        lKind, lHEADId, lHash = "unknown", None, None

        # Check if a git repository
        if exists(join(lSrcDir, '.git')):
            with DirSentry(lSrcDir) as _:

                lKind = 'git'
                try:
                    sh.git('rev-parse', '--git-dir')
                except sh.ErrorReturnCode_128:
                    lKind += ' (broken)'
                    lHEADId = '(unknown)'

                if lKind == 'git':
                    try:
                        lBranch = '/'.join(
                            sh.git('symbolic-ref', 'HEAD').split('/')[2:]
                        ).strip()
                    except sh.ErrorReturnCode_128:
                        lBranch = None

                    try:
                        lTag = sh.git(
                            'describe', '--tags', '--exact-match', 'HEAD'
                        ).strip()
                    except sh.ErrorReturnCode_128:
                        lTag = None

                    lHash = sh.git('rev-parse', '--short=8', 'HEAD').strip() + '...'

                    if lTag is not None:
                        lHEADId = lTag
                    elif lBranch is not None:
                        lHEADId = lBranch
                    else:
                        lHEADId = lHash

                    try:
                        sh.git('diff', '--no-ext-diff', '--quiet').strip()
                    except sh.ErrorReturnCode_1:
                        lHEADId += '*'

                    try:
                        sh.git('diff', '--no-ext-diff', '--cached', '--quiet').strip()
                    except sh.ErrorReturnCode_1:
                        lHEADId += '+'
        elif exists(join(lSrcDir, '.svn')):
            with DirSentry(lSrcDir) as _:
                lKind = 'svn'

                lSVNInfoRaw = sh.svn('info')

                lSVNInfo = {
                    lEntry[0]: lEntry[1].strip()
                    for lEntry in (
                        lLine.split(':', 1)
                        for lLine in lSVNInfoRaw.split('\n')
                        if lLine
                    )
                }

                lHEADId = lSVNInfo['URL'].replace(lSVNInfo['Repository Root'] + '/', '')

                lSVNStatus = sh.svn('status', '-q')
                if len(lSVNStatus):
                    lHEADId += '*'

                lHash = lSVNInfo['Revision']

        lSrcTable.add_row([lSrc, lKind, lHEADId, lHash])
    echo(lSrcTable.draw())


# ------------------------------------------------------------------------------
def create_component(env, component):
    lPathMaker = Pathmaker(env.srcdir, env._verbosity)

    lCmpPath = lPathMaker.getPath(*component)
    if exists(lPathMaker.getPath(*component)):
        secho("ERROR: Component '{}' already exists".format(lCmpPath), fg='red')
        raise click.ClickException("Command aborted")

    for sd in ['src', 'include', 'iprepo', 'addrtab']:
        lPath = lPathMaker.getPath(*component, command=sd)
        mkdir(lPath)
        secho("Folder {} created.".format(lPath), fg='cyan')


# ------------------------------------------------------------------------------
def run(env, pkg, cmd, args):

    if pkg:
        if pkg not in env.sources:
            secho(
                "ERROR: '{}' package not known.\nKnown packages:\n{}".format(
                    pkg, '\n'.join((' * ' + s for s in env.sources))
                ),
                fg='red',
            )
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
        raise click.ClickException(
            "Command '{}' failed with error code {}".format(
                lExc.full_cmd, lExc.exit_code
            )
        )


# ------------------------------------------------------------------------------
def find(env):
    sh.find(env.srcdir, '-name', '*.vhd', _out=sys.stdout)
