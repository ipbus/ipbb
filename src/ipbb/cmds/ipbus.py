
import os
import sh
import sys
import click

from rich.prompt import Confirm
from rich.markup import escape

from os.path import join, split, exists, abspath, splitext, relpath, basename
from ..console import cprint, console
from ..defaults import kProjAreaFile, kProjUserFile
from ..utils import which, DEFAULT_ENCODING
from ..utils import DirSentry, formatDictTable
from .common import addrtab

# ------------------------------------------------------------------------------
def ipbus(ictx):
    pass

# ------------------------------------------------------------------------------
def gendecoders(ictx, aCheckUpToDate, aForce):

    lDecodersDir = 'decoders'

    with DirSentry(ictx.currentproj.path):
        sh.rm('-rf', lDecodersDir)
        # Gather address tables
        addrtab(ictx, aDest=lDecodersDir)

    lGenScript = 'gen_ipbus_addr_decode'

    if not which(lGenScript):
        raise click.ClickException("'{0}' script not found.".format(lGenScript))

    cprint(f"Using {which(lGenScript)}", style='green')

    # ------------------------------------------------------------------------------

    lUpdatedDecoders = []
    lGen = sh.Command(which(lGenScript))
    lErrors = {}
    with DirSentry(join(ictx.currentproj.path, lDecodersDir)):
        for lAddr in ictx.depParser.commands['addrtab']:
            cprint(f"Processing [blue]{basename(lAddr.filepath)}[/blue]")
            # Interested in top-level address tables only
            if not lAddr.toplevel:
                cprint(
                    f"{lAddr.filepath} is not a top-level address table. Decoder will not be generated.",
                    style='cyan',
                )
                continue

            # Generate a new decoder file
            try:
                lGen(basename(lAddr.filepath), _out=sys.stdout, _err=sys.stderr, _tee=True)
            except Exception as lExc:
                cprint(f"Failed to generate decoder for {basename(lAddr.filepath)}", style='red')
                lErrors[lAddr] = lExc
                continue

            lDecoder = f'ipbus_decode_{splitext(basename(lAddr.filepath))[0]}.vhd'
            lTarget = ictx.pathMaker.getPath(
                lAddr.package, lAddr.component, 'src', lDecoder
            )

            diff = sh.colordiff if which('colordiff') else sh.diff

            # Has anything changed?
            try:
                diff('-u', '-I', '^-- START automatically', lTarget, lDecoder)
            except sh.ErrorReturnCode as e:
                cprint(f"[red]{lDecoder}[/red]")
                cprint(escape(e.stdout.decode()), highlight=False)
                import IPython
                IPython.embed()
                lUpdatedDecoders.append((lDecoder, lTarget))

        if lErrors:
            cprint(
                "\nERROR: decoder generation failed",
                style='red',
            )
            for a in sorted(lErrors):
                cprint(' - ' + basename(a.filepath))
                cprint('   ' + lErrors[a].stdout.decode(DEFAULT_ENCODING, "replace"))
            raise SystemExit(-1)



        # ------------------------------------------------------------------------------
        # If no difference between old and newly generated decoders, quit here.
        if not lUpdatedDecoders:
            console.log(
                f"{ictx.currentproj.name}: All ipbus decoders are up-to-date.",
                style='green',
            )
            return

        # ------------------------------------------------------------------------------
        cprint(
            'The following decoders have changed and must be updated:\n'
            + '\n'.join([f" - [red]{d}[/red]" for d,t in lUpdatedDecoders])
            + '\n'
        )
        if aCheckUpToDate:
            raise SystemExit(-1)

        if not aForce and not Confirm.ask("Do you want to continue?"):
            return

        for lDecoder, lTarget in lUpdatedDecoders:
            cprint(sh.cp('-av', lDecoder, lTarget))

        console.log(
            f"{ictx.currentproj.name}: {len(lUpdatedDecoders)} decoders updated.",
            style='green',
        )
# ------------------------------------------------------------------------------
