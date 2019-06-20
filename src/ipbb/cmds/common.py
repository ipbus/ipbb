from __future__ import print_function, absolute_import

import os
import sh
import sys
import click

from click import echo, secho, style, confirm
from os.path import join, split, exists, abspath, splitext, relpath, basename
from ..defaults import kProjAreaFile, kProjUserFile
from ..cli.utils import DirSentry, formatDictTable
from ..tools.common import which


# ------------------------------------------------------------------------------
def cleanup(env):

    _, lSubdirs, lFiles = next(os.walk(env.currentproj.path))
    for f in [kProjAreaFile, kProjUserFile]:
        if f not in lFiles:
            continue

        lFiles.remove(f)

    if lFiles and not click.confirm(
        style(
            "All files and directories in\n'{}'\n will be deleted.\nDo you want to continue?".format(
                env.currentproj.path
            ),
            fg='yellow',
        )
    ):
        return

    if lSubdirs:
        sh.rm('-rv', *lSubdirs, _out=sys.stdout)

    if lFiles:
        sh.rm('-v', *lFiles, _out=sys.stdout)


# ------------------------------------------------------------------------------
def user_config(env, aList, aAdd, aUnset):

    echo("User settings")

    if aAdd:
        lKey, lValue = aAdd
        env.currentproj.usersettings[lKey] = lValue
        env.currentproj.saveUserSettings()

    if aUnset:
        del env.currentproj.usersettings[aUnset]
        env.currentproj.saveUserSettings()

    if env.currentproj.usersettings:
        echo(formatDictTable(env.currentproj.usersettings))


# ------------------------------------------------------------------------------
def addrtab(env, aDest):
    '''Copy address table files into addrtab subfolder'''

    try:
        os.mkdir(aDest)
    except OSError:
        pass

    import sh

    if not env.depParser.commands["addrtab"]:
        secho(
            "\nWARNING no address table files defined in {}.\n".format(
                env.currentproj.name
            ),
            fg='yellow',
        )
        return

    for addrtab in env.depParser.commands["addrtab"]:
        print(sh.cp('-av', addrtab.FilePath, join(aDest, basename(addrtab.FilePath))))
    secho(
        "\n{}: Address table files collected in '{}'.\n".format(
            env.currentproj.name, aDest
        ),
        fg='green',
    )


# ------------------------------------------------------------------------------
def gendecoders(env, aCheckUpToDate):

    lDecodersDir = 'decoders'

    with DirSentry(env.currentproj.path):
        sh.rm('-rf', lDecodersDir)
        # Gather address tables
        addrtab(env, aDest=lDecodersDir)

    lGenScript = 'gen_ipbus_addr_decode'
    lGenToolPath = '/opt/cactus/bin/uhal/tools'
    lGenToolLibPath = '/opt/cactus/lib'

    if not which(lGenScript):

        lPaths = os.environ['PATH'].split() if os.environ['PATH'] else []
        if lGenToolPath not in lPaths:
            lPaths[0:0] = [lGenToolPath]
            os.environ['PATH'] = ':'.join(lPaths)

        if not which(lGenScript):
            raise click.ClickException("'{0}' script not found.".format(lGenScript))

    lLibPaths = (
        os.environ['LD_LIBRARY_PATH'].split() if 'LD_LIBRARY_PATH' in os.environ else []
    )
    if lGenToolLibPath not in lLibPaths:
        lLibPaths[0:0] = [lGenToolLibPath]
        os.environ['LD_LIBRARY_PATH'] = ':'.join(lLibPaths)

    secho("Using " + which(lGenScript), fg='green')

    # ------------------------------------------------------------------------------

    lUpdatedDecoders = []
    lGen = sh.Command(lGenScript)
    with DirSentry(join(env.currentproj.path, lDecodersDir)):
        for lAddr in env.depParser.commands['addrtab']:
            echo("Processing " + style(basename(lAddr.FilePath), fg='blue'))
            # Interested in top-level address tables only
            if not lAddr.TopLevel:
                secho(
                    "{} is not a top-level address table. Decoder will not be generated.".format(
                        lAddr.FilePath
                    ),
                    fg='cyan',
                )
                continue

            # Generate a new decoder file
            lGen(basename(lAddr.FilePath), _out=sys.stdout, _err_to_out=True)
            lDecoder = 'ipbus_decode_{0}.vhd'.format(
                splitext(basename(lAddr.FilePath))[0]
            )
            lTarget = env.pathMaker.getPath(
                lAddr.Package, lAddr.Component, 'src', lDecoder
            )

            diff = sh.colordiff if which('colordiff') else sh.diff

            # Has anything changed?
            try:
                diff('-u', '-I', '^-- START automatically', lTarget, lDecoder)
            except sh.ErrorReturnCode as e:
                print(e.stdout.decode())

                lUpdatedDecoders.append((lDecoder, lTarget))

        # ------------------------------------------------------------------------------
        # If no difference between old and newly generated decoders, quit here.
        if not lUpdatedDecoders:
            secho(
                "\n{}: All ipbus decoders are up-to-date.\n".format(
                    env.currentproj.name
                ),
                fg='green',
            )
            return

        # ------------------------------------------------------------------------------
        echo(
            'The following decoders have changed and must be updated:\n'
            + '\n'.join(map(lambda s: '* ' + style(s[0], fg='blue'), lUpdatedDecoders))
            + '\n'
        )
        if aCheckUpToDate:
            raise SystemExit(-1)

        confirm('Do you want to continue?', abort=True)
        for lDecoder, lTarget in lUpdatedDecoders:
            print(sh.cp('-av', lDecoder, lTarget))

        secho(
            "\n\n{}: {} decoders updated.\n".format(
                env.currentproj.name, len(lUpdatedDecoders)
            ),
            fg='green',
        )


# ------------------------------------------------------------------------------
