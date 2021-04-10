# -*- coding: utf-8 -*-

# Modules
import click
import os
import sh
import hashlib
import collections
import contextlib
import sys
import re

from os.path import (
    join,
    split,
    exists,
    basename,
    abspath,
    splitext,
    relpath,
    isfile,
    isdir,
)
from ..console import cprint
from ..tools.common import which, SmartOpen
from ..depparser import DepFormatter, dep_command_types
from ..utils import DirSentry, printDictTable, printAlienTable
from rich.table import Table, Column
from rich.padding import Padding

# ------------------------------------------------------------------------------
def dep(ictx, proj):
    '''Dependencies command group'''

    lProj = proj if proj is not None else ictx.currentproj.name
    if lProj is not None:
        # Change directory before executing subcommand
        from .proj import cd

        cd(ictx, lProj, False)
        return
    else:
        if ictx.currentproj.name is None:
            raise click.ClickException(
                'Project area not defined. Move into a project area and try again'
            )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def report(ictx, filters):
    '''Summarise the dependency tree of the current project'''

    lCmdHeaders = ['path', 'flags', 'package', 'component', 'lib']

    lFilterFormat = re.compile('([^=]*)=(.*)')
    lFilterFormatErrors = []
    lFieldNotFound = []
    lFilters = []

    for f in filters:
        m = lFilterFormat.match(f)
        if not m:
            lFilterFormatErrors.append(f)
            continue

        if m.group(1) not in lCmdHeaders:
            lFieldNotFound.append(m.group(1))
            continue

        try:
            i = lCmdHeaders.index(m.group(1))
            r = re.compile(m.group(2))
            lFilters.append((i, r))
        except RuntimeError:
            lFilterFormatErrors.append(f)

    if lFilterFormatErrors:
        raise click.ClickException(
            "Filter syntax errors: "
            + ' '.join(['\'' + e + '\'' for e in lFilterFormatErrors])
        )

    if lFieldNotFound:
        raise click.ClickException(
            "Filter syntax errors: fields not found {}. Expected one of {}".format(
                ', '.join("'" + s + "'" for s in lFieldNotFound),
                ', '.join(("'" + s + "'" for s in lCmdHeaders)),
            )
        )


    # return
    lParser = ictx.depParser
    lDepFmt = DepFormatter(lParser)

    cprint('* Variables', style='blue')
    # printDictTable(lParser.vars, aHeader=False)
    printAlienTable(lParser.settings, aHeader=False)

    cprint()
    cprint('* Dep-tree commands', style='blue')

    lPrepend = re.compile('(^|\n)')
    for k in lParser.commands:
        cprint(f'  + {k} ({len(lParser.commands[k])})')
        if not lParser.commands[k]:
            cprint()
            continue

        lCmdTable = Table(*lCmdHeaders, title=f'{k} ({len(lParser.commands[k])})')
        for lCmd in lParser.commands[k]:
            lRow = [
                relpath(lCmd.filepath, ictx.srcdir),
                ','.join(lCmd.flags()),
                lCmd.package,
                lCmd.component,
                lCmd.lib if lCmd.cmd == 'src' else '',
            ]

            if lFilters and not all([rxp.match(lRow[i]) for i, rxp in lFilters]):
                continue

            lCmdTable.add_row(*lRow)

        # cprint(lPrepend.sub(r'\g<1>  ', lCmdTable.draw()))
        cprint(Padding.indent(lCmdTable, 4))
        cprint()

    cprint('Resolved packages & components', style='blue')

    lString = ''

    lString += 'packages: ' + lDepFmt.drawPackages() + '\n'
    lString += 'components:\n'
    lString += lDepFmt.drawComponents()
    cprint(lString+'\n')

    if lParser.errors:
        cprint("Dep tree parsing error(s):", style='red')
        cprint(lDepFmt.drawParsingErrors())

    if lParser.unresolved:
        lString = ''
        if lParser.unresolvedPackages:
            cprint("Unresolved packages:", style='red')
            cprint(lDepFmt.drawUnresolvedPackages())
            cprint()

        # ------
        lCNF = lParser.unresolvedComponents
        if lCNF:
            cprint("Unresolved components:", style='red')
            cprint(lDepFmt.drawUnresolvedComponents())
            cprint()


        # ------

        # ------
        cprint(lString)

    if lParser.unresolvedFiles:
        cprint("Unresolved files:", style='red')

        # cprint(lPrepend.sub(r'\g<1>  ', lDepFmt.drawUnresolvedFiles()))
        cprint(Padding.indent(lDepFmt.drawUnresolvedFiles(), 4))


# ------------------------------------------------------------------------------

def ls(ictx, group: str, output: str):
    '''
    List project files by group
    
    - setup: Project setup scripts
    - src: Code files
    - addrtab: Address tables
    
    :param      ictx:    The ictx
    :type       ictx:    { type_description }
    :param      group:   The group
    :type       group:   str
    :param      output:  The output
    :type       output:  str
    


    :rtype:     None
    '''

    with SmartOpen(output) as lWriter:
        for f in ictx.depParser.commands[group]:
            lWriter(f.filepath)


# ------------------------------------------------------------------------------

def components(ictx, output: str):
    """
    { function_description }

    :param      ictx:    The ictx
    :type       ictx:    { type_description }
    :param      output:  The output
    :type       output:  str
    """

    with SmartOpen(output) as lWriter:
        for lPkt, lCmps in ictx.depParser.packages.items():
            lWriter('[' + lPkt + ']')
            for lCmp in lCmps:
                lWriter(lCmp)
            lWriter()


# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@contextlib.contextmanager
def set_env(**environ):
    """
    Temporarily set the process environment variables.

    >>> with set_env(PLUGINS_DIR=u'test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    lOldEnviron = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(lOldEnviron)


# ------------------------------------------------------------------------------
# ----------------------------
def hash_and_update0g(
    aFilePath, aChunkSize=0x10000, aUpdateHashes=None, aAlgo=hashlib.sha1
):

    # New instance of the selected algorithm
    lHash = aAlgo()

    # Loop ovet the file content
    with open(aFilePath, "rb") as f:
        for lChunk in iter(lambda: f.read(aChunkSize), b''):
            lHash.update(lChunk)

            # Also update other hashes
            for lUpHash in aUpdateHashes:
                lUpHash.update(lChunk)

    return lHash


# ----------------------------


# ----------------------------
def hash_and_update(aPath, aChunkSize=0x10000, aUpdateHashes=None, aAlgo=hashlib.sha1):

    # New instance of the selected algorithm
    lHash = aAlgo()

    if isfile(aPath):
        # Loop ovet the file content
        with open(aPath, "rb") as f:
            for lChunk in iter(lambda: f.read(aChunkSize), b''):
                lHash.update(lChunk)

                # Also update other hashes
                for lUpHash in aUpdateHashes:
                    lUpHash.update(lChunk)
    elif isdir(aPath):
        for root, dirs, files in os.walk(aPath):
            for f in files:
                hash_and_update(f, aChunkSize, aUpdateHashes=aUpdateHashes, aAlgo=aAlgo)

    return lHash


# ----------------------------


def hash(ictx, output, verbose):

    lAlgoName = 'sha1'

    lAlgo = getattr(hashlib, lAlgoName, None)

    # Ensure that the selecte algorithm exists
    if lAlgo is None:
        raise AttributeError('Hashing algorithm {0} is not available'.format(lAlgoName))

    with SmartOpen(output) as lWriter:

        if verbose:
            lTitle = "{0} hashes for project '{1}'".format(
                lAlgoName, ictx.currentproj.name
            )
            lWriter("# " + '=' * len(lTitle))
            lWriter("# " + lTitle)
            lWriter("# " + "=" * len(lTitle))
            lWriter()

        lProjHash = lAlgo()
        lGrpHashes = collections.OrderedDict()
        for lGrp, lCmds in ictx.depParser.commands.items():
            lGrpHash = lAlgo()
            if verbose:
                lWriter("#" + "-" * 79)
                lWriter("# " + lGrp)
                lWriter("#" + "-" * 79)
            for lCmd in lCmds:
                lCmdHash = hash_and_update(
                    lCmd.filepath, aUpdateHashes=[lProjHash, lGrpHash], aAlgo=lAlgo
                ).hexdigest()
                if verbose:
                    lWriter(lCmdHash, lCmd.filepath)

            lGrpHashes[lGrp] = lGrpHash

            if verbose:
                lWriter()

        if verbose:
            lWriter("#" + "-" * 79)
            lWriter("# Per cmd-group hashes")
            lWriter("#" + "-" * 79)
            for lGrp, lHash in lGrpHashes.items():
                lWriter(lHash.hexdigest(), lGrp)
            lWriter()

            lWriter("#" + "-" * 79)
            lWriter("# Global hash for project '" + ictx.currentproj.name + "'")
            lWriter("#" + "-" * 79)
            lWriter(lProjHash.hexdigest(), ictx.currentproj.name)

        if not verbose:
            lWriter(lProjHash.hexdigest())

    return lProjHash


# ------------------------------------------------------------------------------
def archive(ictx):

    import tarfile
    def tarinfo_relpath(tarinfo):
        # Note: the source dir leading '/' [1:] is removed because tarindo names don't have it
        tarinfo.name = relpath(tarinfo.name, ictx.srcdir[1:])
        return tarinfo

    with tarfile.open(f"{ictx.currentproj.name}_src.tar.gz", "w:gz") as tar:
        for c in dep_command_types:
            for f in ictx.depParser.commands[c]:
                print(f.filepath)
                tar.add(f.filepath, filter=tarinfo_relpath)



# ------------------------------------------------------------------------------
