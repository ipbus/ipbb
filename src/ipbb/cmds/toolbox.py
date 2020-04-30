from __future__ import print_function, absolute_import
import click

import re
import ipaddress
import sh
import os

from click import echo, style, secho, confirm
from os.path import basename, dirname, relpath, abspath, exists, splitext, join, isabs, sep, isdir, isfile
from texttable import Texttable

from ..depparser import Pathmaker, DepFileParser


# ------------------------------------------------------------------------------
def toolbox(env):
    '''Miscelaneous useful commands'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def check_depfile(env, verbose, toolset, component, depfile):
    '''Perform basic checks on dependency files'''

    lPackage, lComponent = component
    if depfile is None:
        depfile = basename(lComponent) + ".dep"

    lPathMaker = Pathmaker(env.srcdir, env._verbosity)

    try:
        lParser = DepFileParser(toolset, lPathMaker)
        lParser.parse(lPackage, lComponent, depfile)
    except OSError as lExc:
        raise click.ClickException("Failed to parse dep file - '{}'".format(lExc))

    echo()

    # N.B. Rest of this function is heavily based on implementation of 'dep report' command; assuming
    #   that output of these 2 commands does not significantly diverge, might make sense to implement
    #   command output in a separate function, that's invoked by both commands

    lCmdHeaders = [
        'path',
        'flags',
        'lib',
    ]  # ['path', 'flags', 'package', 'component', 'map', 'lib']
    lFilters = []

    lPrepend = re.compile('(^|\n)')
    if verbose:
        secho('Parsed commands', fg='blue')

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
                # print(lCmd)
                # lCmdTable.add_row([str(lCmd)])
                lRow = [
                    relpath(lCmd.filepath, env.srcdir),
                    ','.join(lCmd.flags()),
                    lCmd.lib,
                ]

                if lFilters and not all([rxp.match(lRow[i]) for i, rxp in lFilters]):
                    continue

                lCmdTable.add_row(lRow)

            echo(lPrepend.sub(r'\g<1>    ', lCmdTable.draw()))
            echo()

        secho('Resolved packages & components', fg='blue')

        string = ''
        for pkg in sorted(lParser.packages):
            string += '  + %s (%d)\n' % (pkg, len(lParser.packages[pkg]))
            for cmp in sorted(lParser.packages[pkg]):
                string += '    > ' + str(cmp) + '\n'
        echo(string)

    if lParser.unresolvedPackages:
        secho('Missing packages:', fg='red')
        echo(str(list(lParser.unresolvedPackages)))

    lCNF = lParser.unresolvedComponents
    if lCNF:
        secho('Missing components:', fg='red')
        string = ''

        for pkg in sorted(lCNF):
            string += '+ %s (%d)\n' % (pkg, len(lCNF[pkg]))

            for cmp in sorted(lCNF[pkg]):
                string += '  > ' + str(cmp) + '\n'
        echo(string)

    lFNF = lParser.unresolvedFiles
    if lFNF:
        secho('Missing files:', fg='red')

        lFNFTable = Texttable(max_width=0)
        lFNFTable.header(
            ['path', 'included by']
        )  # ['path expression','package','component','included by'])
        lFNFTable.set_deco(Texttable.HEADER | Texttable.BORDER)

        for pkg in sorted(lFNF):
            lCmps = lFNF[pkg]
            for cmp in sorted(lCmps):
                lPathExps = lCmps[cmp]
                for pathexp in sorted(lPathExps):

                    lFNFTable.add_row(
                        [
                            relpath(pathexp, env.srcdir),
                            '\n'.join(
                                [relpath(src, env.srcdir) for src in lPathExps[pathexp]]
                            ),
                        ]
                    )
        echo(lPrepend.sub('\g<1>  ', lFNFTable.draw()))
        echo()

    if lParser.unresolvedPackages or lParser.unresolvedComponents or lParser.unresolvedFiles:
        raise click.ClickException(
            "Cannot find 1 or more files referenced by depfile {}".format(
                lPathMaker.getPath(lPackage, lComponent, 'include', depfile)
            )
        )
    elif not verbose:
        echo(
            "No errors found in depfile {}".format(
                lPathMaker.getPath(lPackage, lComponent, 'include', depfile)
            )
        )


# ------------------------------------------------------------------------------
def vhdl_beautify(env, component, path):
    """
    Helper command to beautify vhdl files.

    Beautifies
    - single files
    - folders
    - packages/components
    """
    import ipbb
    import tempfile
    import shutil
    import sys
    from ..tools.common import which

    if not which('emacs'):
        raise click.ClickException(
            'Emacs not found. Please install emacs and try again.'
        )
        
    # Put explicit file paths into a pot
    lAllPaths = [abspath(p) for p in path]

    # Add references to working area paths
    if component:
        lPathmaker = Pathmaker(env.srcdir, 0)

        for c in component:
            lAllPaths.append(str(lPathmaker.getPath(*c)))

    # Chech that they all exist
    lPathsNotFound = [ p for p in lAllPaths if not exists(p)]

    # And complain about the ones that don't
    if lPathsNotFound:
        raise click.ClickException("Couldn't find the following paths: {}".format(', '.join(lPathsNotFound)))

    # Find VHDL files
    lVHDLFiles = []
    for p in lAllPaths:
        if isfile(p) and splitext(p)[1] in ('.vhd', '.vhdl'):
            lVHDLFiles.append(p)
        elif isdir(p):
            for root, dirs, files in os.walk(p):
                for f in files:
                    if not splitext(f)[1] in ('.vhd', '.vhdl'):
                        continue
                    lVHDLFiles.append(join(root, f))

    lVHDLModePath = join(abspath(dirname(ipbb.__file__)), 'externals', 'vhdl-mode-3.38.1')
    print(lVHDLModePath)

    # Create a temporary folder
    lTmpDir = tempfile.mkdtemp()
    lBeautifiedFiles = []

    for f in lVHDLFiles:

        lTmpVHDLPath = join(lTmpDir, f.lstrip(sep))

        if not exists(dirname(lTmpVHDLPath)):
            os.makedirs(dirname(lTmpVHDLPath))

        shutil.copy(f, dirname(lTmpVHDLPath))

        echo('Processing vhdl file ' + style(f, fg="cyan"))
        sh.emacs('--batch', '-q', '--eval', '(setq load-path (cons (expand-file-name "%s") load-path))' % lVHDLModePath, lTmpVHDLPath, '--eval', '(setq vhdl-basic-offset 4)', '-f', 'vhdl-beautify-buffer', _err=sys.stderr)

        diff = sh.colordiff if which('colordiff') else sh.diff
        try:
            diff('-u', f, lTmpVHDLPath)
            print('No beautification needed!')
        except sh.ErrorReturnCode as e:
            print(e.stdout.decode())
            print('Beautified!')
            lBeautifiedFiles.append((f, lTmpVHDLPath))

    echo(
        'The following vhdl files are ready to be beautified:\n'
        + '\n'.join(map(lambda s: '* ' + style(s[0], fg='blue'), lBeautifiedFiles))
        + '\n'
    )
    confirm('Do you want to continue?', abort=True)
    for lTarget, lBeautified in lBeautifiedFiles:
        print(sh.cp('-av', lBeautified, lTarget))

    shutil.rmtree(lTmpDir)

