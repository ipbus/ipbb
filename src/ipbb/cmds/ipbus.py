from __future__ import print_function, absolute_import

import os
import sh
import sys
import click

from click import echo, secho, style, confirm
from os.path import join, split, exists, abspath, splitext, relpath, basename
from ..defaults import kProjAreaFile, kProjUserFile
from ..tools.common import which
from ._utils import DirSentry, formatDictTable
from .common import addrtab

# ------------------------------------------------------------------------------
def ipbus(env):
    pass

# ------------------------------------------------------------------------------
def gendecoders(env, aCheckUpToDate, aForce):

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
    lGen = sh.Command('python').bake(which(lGenScript))
    lErrors = {}
    with DirSentry(join(env.currentproj.path, lDecodersDir)):
        for lAddr in env.depParser.commands['addrtab']:
            echo("Processing " + style(basename(lAddr.filepath), fg='blue'))
            # Interested in top-level address tables only
            if not lAddr.toplevel:
                secho(
                    "{} is not a top-level address table. Decoder will not be generated.".format(
                        lAddr.filepath
                    ),
                    fg='cyan',
                )
                continue

            # Generate a new decoder file
            try:
                lGen(basename(lAddr.filepath), _out=sys.stdout, _err=sys.stderr, _tee=True)
            except Exception as lExc:
                secho('Failed to generate decoder for '+basename(lAddr.filepath), fg='red')
                lErrors[lAddr] = lExc
                continue

            lDecoder = 'ipbus_decode_{0}.vhd'.format(
                splitext(basename(lAddr.filepath))[0]
            )
            lTarget = env.pathMaker.getPath(
                lAddr.package, lAddr.component, 'src', lDecoder
            )

            diff = sh.colordiff if which('colordiff') else sh.diff

            # Has anything changed?
            try:
                diff('-u', '-I', '^-- START automatically', lTarget, lDecoder)
            except sh.ErrorReturnCode as e:
                lUpdatedDecoders.append((lDecoder, lTarget))

        if lErrors:
            secho(
                "\nERROR: decoder generation failed",
                fg='red',
            )
            for a in sorted(lErrors):
                echo(' - ' + basename(a.filepath))
                echo('   ' + lErrors[a].stdout)
            return



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

        if not aForce:
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
