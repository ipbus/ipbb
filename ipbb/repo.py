from __future__ import print_function

# Modules
import click
import os
import ipbb
import subprocess

# Elements
from os.path import join, split, exists, splitext, dirname
from .common import DirSentry, findFileInParents

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
@click.command()
@click.argument('area')
# @click.option('-r', '--repo')
@click.pass_obj
def init(env, area):
  '''Initialise a new firmware development area'''

  print('Setting up new firmware area \''+area+'\'')

  if env.root is not None:
    raise click.ClickException( 'Cannot create a new area inside an existing one %s' % env.root )

  if exists(area):
    raise click.ClickException( 'Directory \'%s\' already exists' % area )

  # Build source code directory
  os.makedirs(join(area, ipbb.kSourceDir))
  os.makedirs(join(area, ipbb.kWorkDir))

  with open( join( area, ipbb.kSignatureFile ),'w' ) as lSignature:
    lSignature.write('\n')
  
  # print( '--->', repo, join( area, ipbb.kSourceDir ) )
  # if not repo:
    # return
  # else:
    # with DirSentry( join( area, ipbb.kSourceDir ) ) as lSentry:
      # subprocess.check_call( ['git', 'clone', repo] )
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
@click.command()
@click.argument( 'path', type=click.Path() )
@click.pass_obj
def cd( env, path ):
  '''Change to new root directory'''

  os.chdir(path)
  env._autodetect()

  print( 'New root directory %s' % os.getcwd() )
  print ( env )
#------------------------------------------------------------------------------

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
@click.option( '-d','--dest', default=None )
@click.option( '-r','--rev', type=click.INT, default=None )
@click.option( '-n', '--dryrun', is_flag=True )
@click.option( '-s', '--sparse', default=None, multiple=True )
@click.pass_obj
def svn(env, repo, dest, rev, dryrun, sparse):
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
  lRepoName = splitext(split(lUrl.path)[-1])[0] if dest is None else dest
  lRepoLocalPath = join(env.src, lRepoName)
  
  if exists(lRepoLocalPath):
    raise click.ClickException( 'Repository already exists \'%s\'' % lRepoLocalPath )
  #------------------------------------------------------------------------------

  #------------------------------------------------------------------------------
  if not sparse:
    lArgs = ['checkout', repo]

    # Append destination directory if defined
    if dest is not None: lArgs.append(dest)

    if rev is not None: lArgs += [ '-r', str(rev) ]
    
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
    lArgs = ['checkout', '--depth=empty', repo]
    
    # Append destination directory if defined
    if dest is not None: lArgs.append(dest)

    if rev is not None: lArgs += [ '-r', str(rev) ]

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


