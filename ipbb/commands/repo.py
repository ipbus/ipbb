from __future__ import print_function

# Modules
import click
import os
# import ipbb
import subprocess


# Elements
from click import echo, style, secho
from os.path import join, split, exists, splitext, dirname

from . import kSourceDir, kProjDir, kWorkAreaCfgFile
from .common import DirSentry, findFileInParents

#------------------------------------------------------------------------------
@click.command()
@click.argument('workarea')
@click.pass_obj
def init(env, workarea):
  '''Initialise a new firmware development area'''

  secho('Setting up new firmware work area \''+workarea+'\'', fg='green')

  if env.workPath is not None:
    raise click.ClickException( 'Cannot create a new work area inside an existing one %s' % env.workPath )

  if exists(workarea):
    raise click.ClickException( 'Directory \'%s\' already exists' % workarea )

  # Build source code directory
  os.makedirs(join(workarea, kSourceDir))
  os.makedirs(join(workarea, kProjDir))

  with open( join( workarea, kWorkAreaCfgFile ),'w' ) as lSignature:
    lSignature.write('\n')
  
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
  if env.workPath is None:
    raise click.ClickException('Build area root directory not found')

  print('adding git repository',repo)

  # Ensure that the destination direcotry doesn't exist
  # Maybe not necessary  
  from urlparse import urlparse
  
  lUrl = urlparse(repo)
  lRepoName = splitext(split(lUrl.path)[-1])[0]
  lRepoLocalPath = join(env.workPath, kSourceDir, lRepoName)
  
  if exists(lRepoLocalPath):
    raise click.ClickException( 'Repository already exists \'%s\'' % lRepoLocalPath )

  lArgs = ['clone', repo]
  if branch is not None:
    lArgs += ['-b', branch]

  # Do the cloning
  with DirSentry( join(env.workPath, kSourceDir) ) as lSentry:
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
  '''Add svn repository REPO to the source area'''

  #------------------------------------------------------------------------------
  # Must be in a build area
  if env.workPath is None:
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
        print ('Executing: ',lCmd)
        subprocess.check_call(lCmd)
  #------------------------------------------------------------------------------


