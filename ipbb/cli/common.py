from __future__ import print_function
# ------------------------------------------------------------------------------

import os
import click
import sh
import sys

from click import secho, confirm, get_current_context
from . import kProjAreaCfgFile

# ------------------------------------------------------------------------------
@click.command()
@click.pass_obj
def cleanup(env):

    _, lSubdirs, lFiles =  next(os.walk(env.projectPath))
    lFiles.remove( kProjAreaCfgFile )


    if not click.confirm("All files in {} will be deleted. Do you want to continue?".format( env.projectPath )):
        return

    print (lSubdirs, lFiles)
    if lSubdirs:
        sh.rm('-rv', *lSubdirs, _out=sys.stdout)
    
    if lFiles:
        sh.rm('-v', *lFiles, _out=sys.stdout)
# ------------------------------------------------------------------------------

