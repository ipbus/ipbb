from __future__ import print_function

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from os.path import join, split, exists, splitext
from common import DirSentry

'''
Commands defined here

* init
* add
  * git
  * svn
* chroot
* chwork
* ls

# Possible evolution

* init
* repo
  * add
    * git
    * svb
  * ls
  * rm
* cd (?)
* work
  * cd
  * ls
'''

#------------------------------------------------------------------------------
def __lswork(env):
  return [ lArea for lArea in next(os.walk(env.root))[1] if exists( join( env.root, lArea, ipbb.kWorkFileName ) ) ]
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.command()
@click.argument('area')
@click.option('-r', '--repo')
@click.pass_obj
def init(env, area, repo):
  '''Initialise a new firmware development area'''

  print('Setting up firmware area \''+area+'\'')


  if env.root is not None:
    raise click.ClickException( 'Cannot create a new area inside an existing one %s' % env.root )

  if exists(area):
    raise click.ClickException( 'Directory \'%s\' already exists' % area )

  # Build source code directory
  os.makedirs(join(area, ipbb.kSourceDir))

  with open( join( area, ipbb.kBuildFileName ),'w' ) as lBuild:
    lBuild.write('\n')
  
  print( '--->', repo, join( area, ipbb.kSourceDir ) )
  if not repo:
    return
  else:
    with DirSentry( join( area, ipbb.kSourceDir ) ) as lSentry:
      subprocess.check_call( ['git', 'clone', repo] )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.command()
@click.pass_obj
def lswork(env):
  '''List existing working areas'''
  
  if env.root is None:
    raise click.ClickException('Build area root directory not found')

  lAreas = __lswork(env)
  print ( 'Root:', env.root )
  print ( 'Work areas:')
  print ( ', '.join( [ ' * '+lArea for lArea in lAreas ] ) )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.command()
@click.argument( 'newroot' )
@click.pass_obj
def chroot(env,newroot):
  '''Change to new root directory'''
    
  with DirSentry( newroot ) as lSentry:
    env._autodetect()

  os.chdir(env.root)
  print( 'New current directory %s' % os.getcwd() )

#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.command()
@click.argument( 'newwork' )
@click.pass_obj
def chwork(env,newwork):

  if newwork[-1] == os.sep: newwork = newwork[:-1]
  lAreas = __lswork(env)
  if newwork not in lAreas:
    raise click.ClickException('Requested work area not found. Available areas %s' % ', '.join(lAreas))

  with DirSentry( join(env.root,newwork) ) as lSentry:
    env._autodetect()

  os.chdir(join(env.root,newwork))
  print( 'New current directory %s' % os.getcwd() )

#------------------------------------------------------------------------------
#
#------------------------------------------------------------------------------
@click.group()
def add():
  pass
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@add.command()
@click.argument( 'repo' )
@click.option( '-b', '--branch', default=None )
@click.pass_obj
def git(env, repo, branch):
  '''Add a git repository to the source area'''
  
  # Must be in a build area
  if env.root is None:
    raise click.ClickException('Build area root directory not found')

  print('adding git repository',repo)

  # Ensure that the destination direcotry doesn't exist
  # Maybe not necessary  
  from urlparse import urlparse
  
  lUrl = urlparse(repo)
  lRepoName = splitext(split(lUrl.path)[-1])[0]
  lRepoLocalPath = join(env.root, ipbb.kSourceDir, lRepoName)
  
  if exists(lRepoLocalPath):
    raise click.ClickException( 'Repository already exists \'%s\'' % lRepoLocalPath )

  lArgs = ['clone', repo]
  if branch is not None:
    lArgs += ['-b', branch]

  # Do the cloning
  with DirSentry( join(env.root, ipbb.kSourceDir) ) as lSentry:
    subprocess.check_call(['git']+lArgs)
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@add.command()
@click.argument( 'repo' )
@click.option( '-n', '--dryrun', is_flag=True )
@click.option( '-s', '--sparse', default=None, multiple=True )
@click.pass_obj
def svn(env, repo, dryrun, sparse):
  '''Add a svn repository/folder to the source area'''

  #------------------------------------------------------------------------------
  # Must be in a build area
  if env.root is None:
    raise click.ClickException('Build area root directory not found')
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  # Stop if the target directory already exists
  print('adding svn repository',repo)
  from urlparse import urlparse
  
  lUrl = urlparse(repo)
  lRepoName = splitext(split(lUrl.path)[-1])[0]
  lRepoLocalPath = join(env.src, lRepoName)
  
  if exists(lRepoLocalPath):
    raise click.ClickException( 'Repository already exists \'%s\'' % lRepoLocalPath )
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  if not sparse:
    lArgs = ['checkout', repo]
    # Do the checkout
    lCmd = ['svn']+lArgs
    print(' '.join(lCmd))
    with DirSentry( env.src ) as lSrcSentry:
      if not dryrun:
        subprocess.check_call(lCmd)
  else:
    print (sparse)
    #------------------------------------------------------------------------------
    # Checkout an empty base folder
    lArgs = ['checkout', repo, '--depth=empty']
    lCmd = ['svn']+lArgs
    print(' '.join(lCmd))
    with DirSentry( env.src ) as lSrcSentry:
      if not dryrun:
        subprocess.check_call(lCmd)
    #------------------------------------------------------------------------------
    lArgs = ['update']
    lCmd = ['svn']+lArgs
    with DirSentry( lRepoLocalPath ) as lSrcSentry:
      for lPath in sparse:
        lTokens = [ lToken for lToken in lPath.split('/') if lToken ]

        lPartials =  [ '/'.join(lTokens[:i+1]) for i,_ in enumerate(lTokens) ]

        for lPartial in lPartials:
          print (lCmd)
          lCmd = ['svn','up','--depth=empty',lPartial]
          subprocess.check_call(lCmd)

        lCmd = ['svn','up','--set-depth=infinity',lPath]
        print (lCmd)
        subprocess.check_call(lCmd)
  #------------------------------------------------------------------------------


