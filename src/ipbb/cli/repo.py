
from ..utils import validateComponent
from ._utils import completeSrcPackage, MutuallyExclusiveOption

# Modules
import click

# ------------------------------------------------------------------------------
@click.command('init', short_help="Initialise a new working area.")
@click.argument('directory')
@click.pass_obj
def init(env, directory):
    '''Initialise a new firmware development area'''
    from ..cmds.repo import init
    init(env, directory)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@click.command()
@click.option('-v', '--verbose', count=True, help="Verbosity")
@click.pass_obj
def info(env, verbose):
    '''Print a brief report about the current working area'''
    from ..cmds.repo import info
    info(env, verbose)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@click.group('add', short_help="Add source packages.")
@click.pass_obj
def add(env):
    '''Add a new package to the source area'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    from ..cmds.repo import add
    add(env)

# ------------------------------------------------------------------------------
@add.command('git', short_help="Add new source package from a git repository")
@click.argument('repo')

@click.option('-b',
              '--branch',
              default=None,
              help='Git branch or tag to clone',
              cls=MutuallyExclusiveOption,
              mutually_exclusive=["revision"])
@click.option('-r',
              '--revision',
              default=None,
              help='Git revision ID to clone',
              cls=MutuallyExclusiveOption,
              mutually_exclusive=["branch"])
@click.option('-d', '--dest', default=None, help="Destination directory")
@click.pass_obj
def git(env, repo, branch, revision, dest):
    '''Add a git repository to the source area'''
    from ..cmds.repo import git
    git(env, repo, branch, revision, dest)


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
    from ..cmds.repo import svn
    svn(env, repo, dest, rev, dryrun, sparse)


# ------------------------------------------------------------------------------
@add.command('tar', short_help="Add new source package from tarball.")
@click.argument('repo')
@click.option('-d', '--dest', default=None, help='Destination folder')
@click.option('-s', '--strip', type=int, default=None, help='Strip <n> level of directories when unpacking.')
@click.pass_obj
def tar(env, repo, dest, strip):
    '''Add a tarball-ed package to the source area'''
    from ..cmds.repo import tar
    tar(env, repo, dest, strip)


# ------------------------------------------------------------------------------
@add.command('symlink', short_help="Add new source as symlink.")
@click.argument('path', type=click.Path(exists=True))
@click.pass_obj
def symlink(env, path):
    '''Add a tarball-ed package to the source area'''
    from ..cmds.repo import symlink
    symlink(env, path)


# ------------------------------------------------------------------------------
@click.group('srcs', short_help="Utility commands to handle source packages.")
@click.pass_obj
def srcs(env):
    pass

# ------------------------------------------------------------------------------
@srcs.command('info', short_help="Information of the status of source packages.")
@click.pass_obj
def srcs_info(env):
    from ..cmds.repo import srcs_info
    srcs_info(env)


# ------------------------------------------------------------------------------
@srcs.command('reset', short_help="Run setup sequence on a source package")
@click.argument('pkg', default=None, autocompletion=completeSrcPackage)
@click.pass_obj
def srcs_reset(env, pkg):
    '''Run setup sequence on a source package
    
    PKG : Name of the package to run the sequence of.
    '''
    from ..cmds.repo import _repoInit, _repoReset
    _repoReset(env, pkg)
    _repoInit(env, pkg)

# ------------------------------------------------------------------------------
@srcs.command('create-component', short_help="Create the skeleton of a new component.")
@click.argument('component', callback=validateComponent)
@click.pass_obj
def srcs_create_component(env, component):
    from ..cmds.repo import srcs_create_component
    srcs_create_component(env, component)


# ------------------------------------------------------------------------------
@srcs.command('run', short_help="Run stuff")
@click.option('-p', '--pkg', default=None, autocompletion=completeSrcPackage)
@click.argument('cmd', nargs=1)
@click.argument('args', nargs=-1)
@click.pass_obj
def srcs_run(env, pkg, cmd, args):
    """
    Execute a shell command in the package folder.
    """
    from ..cmds.repo import srcs_run
    srcs_run(env, pkg, cmd, args)


# ------------------------------------------------------------------------------
@srcs.command('find', short_help="Find src files.")
@click.pass_obj
def srcs_find(env):
    from ..cmds.repo import srcs_find
    srcs_find(env)
