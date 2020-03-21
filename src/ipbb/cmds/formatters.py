# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
from future.utils import raise_with_traceback
# ------------------------------------------------------------------------------

from texttable import Texttable
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


class DepFormatter(object):
    """docstring for DepFormatter"""
    def __init__(self, parser):
        super(DepFormatter, self).__init__()
        self.parser = parser

    def _drawPackages(self, aPkgs):
        if not aPkgs:
            return ''

        return ' '.join(list(aPkgs))

    def drawPackages(self):
        return self._drawPackages(self.parser.packages)

    def drawUnresolvedPackages(self):
        return self._drawPackages(self.parser.unresolvedPackages)

    def _drawComponents(self, aPkgs):
        if not aPkgs:
            return ''

        lString = ''
        for pkg in sorted(aPkgs):
            lString += '+ %s (%d)\n' % (pkg, len(aPkgs[pkg]))
            lSortCmps = sorted(aPkgs[pkg])
            for cmp in lSortCmps[:-1]:
                lString += u'  ├──' + str(cmp) + '\n'
            lString += u'  └──' + str(lSortCmps[-1]) + '\n'

        return lString[:-1]

    def drawComponents(self):
        return self._drawComponents(self.parser.packages)

    def drawUnresolvedComponents(self):
        return self._drawComponents(self.parser.unresolvedComponents)

    def drawUnresolvedFiles(self):
        lFNF = self.parser.unresolvedFiles
        if not lFNF:
            return ""

        lFNFTable = Texttable(max_width=0)
        lFNFTable.header(['path expression', 'package', 'component', 'included by'])
        lFNFTable.set_deco(Texttable.HEADER | Texttable.BORDER)

        for pkg in sorted(lFNF):
            lCmps = lFNF[pkg]
            for cmp in sorted(lCmps):
                lPathExps = lCmps[cmp]
                for pathexp in sorted(lPathExps):
                    lFNFTable.add_row(
                        [
                            relpath(pathexp, self.parser.rootdir),
                            pkg,
                            cmp,
                            '\n'.join(
                                [(relpath(src, self.parser.rootdir) if src != '__top__' else '(top)') for src in lPathExps[pathexp]]
                            ),
                        ]
                    )
        return lFNFTable.draw()

    def drawParsingErrors(self):
        """
        Draws a text table detailing parsing errors.
        
        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """

        lErrors = self.parser.errors

        lErrTable = Texttable(max_width=0)
        lErrTable.header(['dep file', 'line', 'error'])
        lErrTable.set_deco(Texttable.HEADER | Texttable.BORDER)

        for lPkg, lCmp, lDepName, lDepPath, lLineNo, lLine, lErr in lErrors:
            
            lErrTable.add_row(
                [
                    relpath(lDepPath, self.parser.rootdir)+':'+str(lLineNo),
                    "'"+lLine+"'",
                    str(lErr),
                ]
            )

        return lErrTable.draw()

