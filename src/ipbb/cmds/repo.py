
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
from ..depparser import Pathmaker
from ..tools.common import mkdir
from ._utils import DirSentry, findFileInParents, raiseError, formatDictTable
from .formatters import DepFormatter
from .proj import info as proj_info
from urllib.parse import urlparse
from distutils.dir_util import mkpath
from texttable import Texttable


# ------------------------------------------------------------------------------
def init(ictx, directory):
    '''Initialise a new firmware development area'''

    secho('Setting up new firmware work area \'' + directory + '\'', fg='green')

    if ictx.work.path is not None:
        raise click.ClickException(
            'Cannot create a new work area inside an existing one %s' % ictx.work.path
        )

    if exists(directory) and os.listdir(directory):
        raise click.ClickException('Directory \'%s\' already exists and it\'s not empty' % directory)

    # Build source code directory
    mkpath(join(directory, kSourceDir))
    mkpath(join(directory, kProjDir))

    with open(join(directory, kWorkAreaFile), 'w') as lSignature:
        lSignature.write('\n')


# ------------------------------------------------------------------------------
def info(ictx, verbose):
    '''Print a brief report about the current working area'''

    if not ictx.work.path:
        secho('ERROR: No ipbb work area detected', fg='red')
        return

    echo()
    secho("ipbb waironment", fg='blue')
    # echo  ( "----------------")

    lEnvTable = Texttable(max_width=0)
    lEnvTable.add_row(["Work path", ictx.work.path])
    if ictx.currentproj.path:
        lEnvTable.add_row(["Project path", ictx.currentproj.path])
    echo(lEnvTable.draw())

    echo()
    srcs_info(ictx)

    echo()
    proj_info(ictx)

    if not ictx.currentproj.path:
        return

    echo()

    if not ictx.currentproj.settings:
        return

    secho("Project '%s'" % ictx.currentproj.name, fg='blue')

    echo(formatDictTable(ictx.currentproj.settings, aHeader=False))

    echo()

    if ictx.currentproj.usersettings:
        secho("User settings", fg='blue')
        echo(formatDictTable(ictx.currentproj.usersettings, aHeader=False))

        echo()

    lParser = ictx.depParser
    lDepFmt = DepFormatter(lParser)

    if lParser.errors:
        secho("Dep tree parsing error(s):", fg='red')
        echo(lDepFmt.drawParsingErrors())
        echo()

    secho("Dependecy tree elements", fg='blue')
    echo(lDepFmt.drawDeptreeCommandsSummary())

    echo()

    if lParser.unresolved:
        secho("Unresolved item(s)", fg='red')
        echo(lDepFmt.drawUnresolvedSummary())

        echo()
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def add(ictx):
    '''Add a new package to the source area'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if ictx.work.path is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def _repoInit(ictx, dest):

    if dest not in ictx.sources:
        secho(f'Source package {dest} not found', fg='red')
        echo('Available repositories:')
        for lPkg in ictx.sources:
            echo(' - ' + lPkg)

        raiseError("Source package {} not found".format(dest))

    initPars = ictx.srcinfo[dest].setupsettings.get('init', None)
    if initPars is None:
        echo("No init procedure defined.")
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

    with sh.pushd(join(ictx.srcdir, dest)):
        # TODO: add error handling
        # Show the list of commands
        # In green the commands executed successfully
        # In red the failed one
        # In white the remaining commands
        for cmd in cmds:
            secho('> '+' '.join(cmd), fg='cyan')
            sh.Command(cmd[0])(*cmd[1:], _out=sys.stdout)

# ------------------------------------------------------------------------------
def _repoReset(ictx, dest):

    if dest not in ictx.sources:
        secho(f"Source package {dest} not found", fg='red')
        echo('Available repositories:')
        for lPkg in ictx.sources:
            echo(' - ' + lPkg)

        raiseError("Source package {} not found".format(dest))

    # setupPath = join(ictx.srcdir, dest, kRepoSetupFile)
    # if not exists(setupPath):
    #     secho('No repository setup file found in {}. Skipping'.format(dest), fg='blue')
    #     return
    # secho('Resetting up {}'.format(dest), fg='blue')

    setupCfg = None
    with open(setupPath, 'r') as f:
        setupCfg = yaml.safe_load(f)

    resetPars = ictx.srcinfo[dest].setupsettings.get('reset', None)
    if resetPars is None:
        echo("No reset procedure defined.")
        return

    cmds = [ l.split() for l in setupCfg ]

    # ensure that all commands exist
    missingCmds = [(i, cmd) for i, cmd in enumerate(cmds) if not sh.which(cmd[0])]
    if missingCmds:
        secho('Some setup commands have not been found', fg='red')
        for i, cmd in missingCmds:
            echo(' - {} (line {})'.format(cmd, i))

        raiseError("Setup commands not found".format(dest))

    with sh.pushd(join(ictx.srcdir, dest)):
        # TODO: add error handling
        # Show the list of commands
        # In green the commands executed successfully
        # In red the failed one
        # In white the remaining commands
        for cmd in cmds:
            secho('> '+' '.join(cmd), fg='cyan')
            sh.Command(cmd[0])(*cmd[1:], _out=sys.stdout)


# ------------------------------------------------------------------------------
def git(ictx, repo, branch, revision, dest):
    '''Add a git repository to the source area'''

    echo('Adding git repository ' + style(repo, fg='blue'))

    # Ensure that the destination direcotry doesn't exist
    # Maybe not necessary

    lUrl = urlparse(repo)
    # Strip '.git' at the end
    lRepoName = splitext(basename(lUrl.path))[0] if dest is None else dest
    lRepoLocalPath = join(ictx.work.path, kSourceDir, lRepoName)

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

    sh.git(*lArgs, _out=sys.stdout, _cwd=ictx.srcdir)

    # NOTE: The mutual exclusivity of checking out a branch and
    # checkout out a revision should have been handled at the CLI
    # option handling stage.
    if branch is not None:

        echo('Checking out branch/tag ' + style(branch, fg='blue'))
        sh.git('checkout', branch, '-q', _out=sys.stdout, _cwd=lRepoLocalPath)

    elif revision is not None:
        echo('Checking out revision ' + style(revision, fg='blue'))
        try:
            sh.git('checkout', revision, '-q', _out=sys.stdout, _cwd=lRepoLocalPath)
        except Exception as err:
            # NOTE: The assumption here is that the failed checkout
            # did not alter the state of the cloned repo in any
            # way. (This appears to be the case from experience but no
            # hard reference could be found.)
            secho("Failed to check out requested revision." \
                  " Staying on default branch.", fg='red')

    secho(
        'Repository \'{}\' successfully cloned to:\n  {}'.format(
            lRepoName, join(ictx.srcdir, lRepoName)
        ),
        fg='green',
    )

    _repoInit(ictx, lRepoName)


# ------------------------------------------------------------------------------
def svn(ictx, repo, dest, rev, dryrun, sparse):
    '''Add a svn repository REPO to the source area'''

    lUrl = urlparse(repo)
    lRepoName = splitext(basename(lUrl.path))[0] if dest is None else dest
    # -------------------------------------------------------------------------
    # Stop if the target directory already exists
    echo('Adding svn repository ' + style(repo, fg='blue'))

    lRepoLocalPath = join(ictx.srcdir, lRepoName)

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
            sh.svn(*lArgs, _out=sys.stdout, _cwd=ictx.srcdir)
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
            sh.svn(*lArgs, _out=sys.stdout, _cwd=ictx.srcdir)
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

    _repoInit(ictx, lRepoName)

    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def tar(ictx, repo, dest, strip):
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
    lRepoLocalPath = join(ictx.work.path, kSourceDir, lRepoName)

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

    _repoInit(ictx, lRepoName)


# ------------------------------------------------------------------------------
def symlink(ictx, path):

    lRepoName = basename(path)
    lRepoLocalPath = join(ictx.srcdir, lRepoName)

    if exists(lRepoLocalPath):
        raise click.ClickException('Repository already exists \'%s\'' % lRepoLocalPath)

    echo(
        'Adding symlink '
        + style(abspath(path), fg='blue')
        + ' as '
        + style(lRepoName, fg='blue')
    )

    sh.ln('-s', abspath(path), _cwd=ictx.srcdir )


# ------------------------------------------------------------------------------
def srcs(ictx):
    pass

# ------------------------------------------------------------------------------
def _git_info():
    lHEADId, lHash = None, None

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

    return lHEADId, lHash

# ------------------------------------------------------------------------------
def _svn_info():
    lHEADId, lHash = None, None

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

    return lHEADId, lHash

# ------------------------------------------------------------------------------
def srcs_info(ictx):

    if not ictx.work.path:
        secho('ERROR: No ipbb work area detected', fg='red')
        return

    echo()
    secho("Firmware Packages", fg='blue')
    lSrcs = ictx.sources
    if not lSrcs:
        return

    lSrcTable = Texttable(max_width=0)
    lSrcTable.set_deco(Texttable.HEADER | Texttable.BORDER)
    lSrcTable.set_chars(['-', '|', '+', '-'])
    lSrcTable.header(['name', 'kind', 'version', 'hash'])
    for lSrc in lSrcs:
        lSrcDir = join(ictx.srcdir, lSrc)

        lKind, lHEADId, lHash = "unknown", None, None

        # Check if a git repository
        if exists(join(lSrcDir, '.git')):
            with DirSentry(lSrcDir) as _:

                lKind = 'git'
                try:
                    sh.git('rev-parse', '--git-dir')
                except sh.ErrorReturnCode_128:
                    lSrcTable.add_row([lSrc, lKind+' (broken)', '(unknown)', None])
                    continue

                lHEADId, lHash = _git_info()
                lSrcTable.add_row([lSrc, lKind, lHEADId, lHash])

                lSubmods = sh.git('submodule').strip()
                if not lSubmods:
                    continue

                for _, lSubModDir, _ in (l.split() for l in lSubmods.split('\n')):
                    print(lSubModDir)
                    with DirSentry(join(lSrcDir,lSubModDir)) as _:
                        lHEADId, lHash = _git_info()
                        lSrcTable.add_row([u'  └──'+basename(lSubModDir), lKind, lHEADId, lHash])

        elif exists(join(lSrcDir, '.svn')):
            with DirSentry(lSrcDir) as _:
                lKind = 'svn'

                lHEADId, lHash = _svn_info()
                lSrcTable.add_row([lSrc, lKind, lHEADId, lHash])
        else:
            lSrcTable.add_row([lSrc, lKind, lHEADId, lHash])


    echo(lSrcTable.draw())


# ------------------------------------------------------------------------------
def srcs_create_component(ictx, component):
    lPathMaker = Pathmaker(ictx.srcdir, ictx._verbosity)

    lCmpPath = lPathMaker.getPath(*component)
    if exists(lPathMaker.getPath(*component)):
        secho("ERROR: Component '{}' already exists".format(lCmpPath), fg='red')
        raise click.ClickException("Command aborted")

    for sd in ['src', 'include', 'iprepo', 'addrtab']:
        lPath = lPathMaker.getPath(*component, command=sd)
        mkdir(lPath)
        secho("Folder {} created.".format(lPath), fg='cyan')


# ------------------------------------------------------------------------------
def srcs_run(ictx, pkg, cmd, args):

    if pkg:
        if pkg not in ictx.sources:
            secho(
                "ERROR: '{}' package not known.\nKnown packages:\n{}".format(
                    pkg, '\n'.join((' * ' + s for s in ictx.sources))
                ),
                fg='red',
            )
            raise click.ClickException("Command failed")
        wd = join(ictx.srcdir, pkg)
    else:
        wd = ictx.srcdir

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
def srcs_find(ictx):
    sh.find(ictx.srcdir, '-name', '*.vhd', _out=sys.stdout)
