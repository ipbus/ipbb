from __future__ import print_function
import click

import re
import ipaddress
import sh

from click import echo, style, secho
from os.path import basename, dirname, relpath, abspath, exists, splitext, join, isabs, sep
from texttable import Texttable

from ...depparser.Pathmaker import Pathmaker
from ...depparser.DepFileParser import DepFileParser


# ------------------------------------------------------------------------------
def toolbox(env):
    '''Miscelaneous useful commands'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def check_depfile(env, verbose, component, depfile, toolset):
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
        'map',
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
                    relpath(lCmd.FilePath, env.srcdir),
                    ','.join(lCmd.flags()),
                    lCmd.Map,
                    lCmd.Lib,
                ]

                if lFilters and not all([rxp.match(lRow[i]) for i, rxp in lFilters]):
                    continue

                lCmdTable.add_row(lRow)

            echo(lPrepend.sub('\g<1>    ', lCmdTable.draw()))
            echo()

        secho('Resolved packages & components', fg='blue')

        string = ''
        for pkg in sorted(lParser.components):
            string += '  + %s (%d)\n' % (pkg, len(lParser.components[pkg]))
            for cmp in sorted(lParser.components[pkg]):
                string += '    > ' + str(cmp) + '\n'
        echo(string)

    if lParser.missingPackages:
        secho('Missing packages:', fg='red')
        echo(str(list(lParser.missingPackages)))

    lCNF = lParser.missingComponents
    if lCNF:
        secho('Missing components:', fg='red')
        string = ''

        for pkg in sorted(lCNF):
            string += '+ %s (%d)\n' % (pkg, len(lCNF[pkg]))

            for cmp in sorted(lCNF[pkg]):
                string += '  > ' + str(cmp) + '\n'
        echo(string)

    lFNF = lParser.missingFiles
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

    if lParser.missingPackages or lParser.missingComponents or lParser.missingFiles:
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
def vhdl_beautify(env):
    """
    emacs --batch -q --e '(setq load-path (cons (expand-file-name "vhdl-mode-3.38.1") load-path))'  /home/ale/devel/emp-fwk/build_ku115/src/emp-fwk/components/payload/firmware/hdl/emp_payload.vhd -f 'vhdl-beautify-buffer'
    """
    if env.currentproj.name is None:
        raise click.ClickException(
            'Project area not defined. Move to a project area and try again'
        )

    import ipbb
    import sys
    import tempfile
    import shutil
    import os
    from ...tools.common import which
    
    lDepFileParser = env.depParser

    lVHDLFiles = [ src.FilePath for src in lDepFileParser.commands['src'] if splitext(src.FilePath)[1] in ['.vhd', '.vhdl']]
    lVHDLModePath = join(abspath(dirname(ipbb.__file__)), 'data', 'vhdl-mode-3.38.1')

    lTmpDir = tempfile.mkdtemp()
    print(lTmpDir)
    lBeautifiedFiles = []

    for f in lVHDLFiles:

        lTmpVHDLPath = join(lTmpDir, f.lstrip(sep))

        if not exists(dirname(lTmpVHDLPath)):
            os.makedirs(dirname(lTmpVHDLPath))

        shutil.copy(f, dirname(lTmpVHDLPath))

        print('Processing',f)
        sh.emacs('--batch', '-q', '--eval', '(setq load-path (cons (expand-file-name "%s") load-path))' % lVHDLModePath, lTmpVHDLPath, '-f', 'vhdl-beautify-buffer')

        diff = sh.colordiff if which('colordiff') else sh.diff
        try:
            diff('-u', f, lTmpVHDLPath)
            print('No beautification needed!')
        except sh.ErrorReturnCode as e:
            print(e.stdout)
            print('Beautified!')
            lBeautifiedFiles.append((f, lTmpVHDLPath))
    shutil.rmtree(lTmpDir)

    print (lBeautifiedFiles)
