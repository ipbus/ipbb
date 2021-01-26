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
from ..tools.common import which, SmartOpen
from .formatters import DepFormatter
from ._utils import DirSentry, printDictTable, printAlienTable
from click import echo, secho, style, confirm
from texttable import Texttable

# ------------------------------------------------------------------------------
def dep(env, proj):
    '''Dependencies command group'''

    lProj = proj if proj is not None else env.currentproj.name
    if lProj is not None:
        # Change directory before executing subcommand
        from .proj import cd

        cd(env, lProj, False)
        return
    else:
        if env.currentproj.name is None:
            raise click.ClickException(
                'Project area not defined. Move into a project area and try again'
            )


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def report(env, filters):
    '''Summarise the dependency tree of the current project'''

    lCmdHeaders = ['path', 'flags', 'package', 'component', 'lib']

    lFilterFormat = re.compile('([^=]*)=(.*)')
    lFilterFormatErrors = []
    lFieldNotFound = []
    lFilters = []

    # print ( filters )

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
    lParser = env.depParser
    lDepFmt = DepFormatter(lParser)

    secho('* Variables', fg='blue')
    # printDictTable(lParser.vars, aHeader=False)
    printAlienTable(lParser.config, aHeader=False)

    echo()
    secho('* Dep-tree commands', fg='blue')

    lPrepend = re.compile('(^|\n)')
    for k in lParser.commands:
        echo('  + {0} ({1})'.format(k, len(lParser.commands[k])))
        if not lParser.commands[k]:
            echo()
            continue

        lCmdTable = Texttable(max_width=0)
        lCmdTable.header(lCmdHeaders)
        lCmdTable.set_deco(Texttable.HEADER | Texttable.BORDER)
        lCmdTable.set_chars(['-', '|', '+', '-'])
        for lCmd in lParser.commands[k]:
            lRow = [
                relpath(lCmd.filepath, env.srcdir),
                ','.join(lCmd.flags()),
                lCmd.package,
                lCmd.component,
                lCmd.lib if lCmd.cmd == 'src' else '',
            ]

            if lFilters and not all([rxp.match(lRow[i]) for i, rxp in lFilters]):
                continue

            lCmdTable.add_row(lRow)

        echo(lPrepend.sub(r'\g<1>  ', lCmdTable.draw()))
        echo()

    secho('Resolved packages & components', fg='blue')

    lString = ''

    # lString += '+----------------------------------+\n'
    # lString += '|  Resolved packages & components  |\n'
    # lString += '+----------------------------------+\n'
    lString += 'packages: ' + lDepFmt.drawPackages() + '\n'
    lString += 'components:\n'
    lString += lDepFmt.drawComponents()
    echo(lString+'\n')

    if lParser.errors:
        secho("Dep tree parsing error(s):", fg='red')
        echo(lDepFmt.drawParsingErrors())

    if lParser.unresolved:
        lString = ''
        if lParser.unresolvedPackages:
            secho("Unresolved packages:", fg='red')
            echo(lDepFmt.drawUnresolvedPackages())
            echo()

        # ------
        lCNF = lParser.unresolvedComponents
        if lCNF:
            secho("Unresolved components:", fg='red')
            echo(lDepFmt.drawUnresolvedComponents())
            echo()


        # ------

        # ------
        echo(lString)

    if lParser.unresolvedFiles:
        secho("Unresolved files:", fg='red')

        echo(lPrepend.sub(r'\g<1>  ', lDepFmt.drawUnresolvedFiles()))


# ------------------------------------------------------------------------------
def ls(env, group, output):
    '''List project files by group

    - setup: Project setup scripts
    - src: Code files
    - addrtab: Address tables 
    - cgpfile: ?
    '''

    with SmartOpen(output) as lWriter:
        for addrtab in env.depParser.commands[group]:
            lWriter(addrtab.filepath)


# ------------------------------------------------------------------------------
def components(env, output):

    with SmartOpen(output) as lWriter:
        for lPkt, lCmps in env.depParser.packages.items():
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
def hashAndUpdate0g(
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
def hashAndUpdate(aPath, aChunkSize=0x10000, aUpdateHashes=None, aAlgo=hashlib.sha1):

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
                hashAndUpdate(f, aChunkSize, aUpdateHashes=aUpdateHashes, aAlgo=aAlgo)

    return lHash


# ----------------------------


def hash(env, output, verbose):

    lAlgoName = 'sha1'

    lAlgo = getattr(hashlib, lAlgoName, None)

    # Ensure that the selecte algorithm exists
    if lAlgo is None:
        raise AttributeError('Hashing algorithm {0} is not available'.format(lAlgoName))

    with SmartOpen(output) as lWriter:

        if verbose:
            lTitle = "{0} hashes for project '{1}'".format(
                lAlgoName, env.currentproj.name
            )
            lWriter("# " + '=' * len(lTitle))
            lWriter("# " + lTitle)
            lWriter("# " + "=" * len(lTitle))
            lWriter()

        lProjHash = lAlgo()
        lGrpHashes = collections.OrderedDict()
        for lGrp, lCmds in env.depParser.commands.items():
            lGrpHash = lAlgo()
            if verbose:
                lWriter("#" + "-" * 79)
                lWriter("# " + lGrp)
                lWriter("#" + "-" * 79)
            for lCmd in lCmds:
                lCmdHash = hashAndUpdate(
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
            lWriter("# Global hash for project '" + env.currentproj.name + "'")
            lWriter("#" + "-" * 79)
            lWriter(lProjHash.hexdigest(), env.currentproj.name)

        if not verbose:
            lWriter(lProjHash.hexdigest())

    return lProjHash


# ------------------------------------------------------------------------------
def archive(env):
    print('archive')


# ------------------------------------------------------------------------------
