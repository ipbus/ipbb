from __future__ import print_function
# ------------------------------------------------------------------------------

import os
import click
import sh
import sys

from click import echo, secho, style, confirm, get_current_context
from os.path import join, split, exists, basename, abspath, splitext, relpath, basename
from . import kProjAreaCfgFile
from .tools import DirSentry
from ..tools.common import which

# ------------------------------------------------------------------------------
@click.command()
@click.pass_obj
def cleanup(env):

    _, lSubdirs, lFiles =  next(os.walk(env.projectPath))
    lFiles.remove( kProjAreaCfgFile )


    if not click.confirm(style("All files and directories in\n'{}'\n will be deleted.\nDo you want to continue?".format( env.projectPath ), fg='yellow')):
        return

    print (lSubdirs, lFiles)
    if lSubdirs:
        sh.rm('-rv', *lSubdirs, _out=sys.stdout)
    
    if lFiles:
        sh.rm('-v', *lFiles, _out=sys.stdout)
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.command()
@click.pass_obj
@click.option('-o', '--output', default='addrtab')
def addrtab(env, output):
    '''Copy address table files into addrtab subfolder'''

    try:
        os.mkdir(output)
    except OSError:
        pass

    import sh
    for addrtab in env.depParser.CommandList["addrtab"]:
        print(sh.cp('-av', addrtab.FilePath,
                    join(output, basename(addrtab.FilePath))
                    ))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@click.command()
@click.pass_context
def gendecoders(ctx):

    lDecodersDir = 'decoders'
    # Extract context
    env = ctx.obj

    with DirSentry(env.projectPath) as lProjDir:
        sh.rm('-rf', lDecodersDir)
        # Gather address tables
        ctx.invoke(addrtab, output=lDecodersDir)

    # ------------------------------------------------------------------------------
    # TODO: Clean me up
    lGenScript = 'gen_ipbus_addr_decode'
    if not which(lGenScript):
        os.environ['PATH'] = '/opt/cactus/bin/uhal/tools:' + os.environ['PATH']
        if not which(lGenScript):
            raise click.ClickException(
                "'{0}' script not found.".format(lGenScript))

    if '/opt/cactus/lib' not in os.environ['LD_LIBRARY_PATH'].split(':'):
        os.environ['LD_LIBRARY_PATH'] = '/opt/cactus/lib:' + \
            os.environ['LD_LIBRARY_PATH']


    lGenScript = 'gen_ipbus_addr_decode'
    lGenToolPath = '/opt/cactus/bin/uhal/tools'
    lGenToolLibPath = '/opt/cactus/lib'

    if not which(lGenScript):

        lPaths = os.environ['PATH'].split() if os.environ['PATH'] else []
        if lGenToolPath not in lPaths:
            lPaths[0:0] = [lGenToolPath]

        lLibPaths = os.environ['LD_LIBRARY_PATH'].split() if os.environ['LD_LIBRARY_PATH'] else []
        if lGenToolLibPath not in lLibPaths:
            lLibPaths[0:0] = [lGenToolLibPath]

        if not which(lGenScript):
            raise click.ClickException(
                "'{0}' script not found.".format(lGenScript))

    # ------------------------------------------------------------------------------

    lUpdatedDecoders = []
    lGen = sh.Command(lGenScript)
    with DirSentry(join(env.projectPath, lDecodersDir)) as lProjDir:
        for lAddr in env.depParser.CommandList['addrtab']:
            echo("Processing "+style(basename(lAddr.FilePath), fg='blue'))
            # Interested in top-level address tables only
            if not lAddr.TopLevel:
                continue

            # Generate a new decoder file
            lGen(basename(lAddr.FilePath), _out=sys.stdout, _err_to_out=True)
            lDecoder = 'ipbus_decode_{0}.vhd'.format(
                splitext(basename(lAddr.FilePath))[0])
            lTarget = env.pathMaker.getPath(
                lAddr.Package, lAddr.Component, 'src', lDecoder)


            diff = sh.colordiff if which('colordiff') else sh.diff

            # Has anything changed?
            try:
                diff('-u', '-I', '^-- START automatically', lTarget, lDecoder)
            except sh.ErrorReturnCode as e:
                print (e.stdout)

                lUpdatedDecoders.append((lDecoder, lTarget))

        # ------------------------------------------------------------------------------
        # If no difference between old and newly generated decoders, quit here.
        if not lUpdatedDecoders:
            print ('All ipbus decoders are up-to-date')
            return
        # ------------------------------------------------------------------------------

        echo (
            'The following decoders have changed and must be updated:\n' +
            '\n'.join(map(lambda s: '* ' + style(s[0], fg='blue'), lUpdatedDecoders)) +
            '\n'
        )
        confirm('Do you want to continue?', abort=True)
        for lDecoder, lTarget in lUpdatedDecoders:
            print (sh.cp('-av', lDecoder, lTarget))
# ------------------------------------------------------------------------------
