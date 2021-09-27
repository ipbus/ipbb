from rich.table import Table, Column
from rich.panel import Panel
from rich.tree import Tree

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
from ._definitions import dep_command_types


class DepFormatter(object):
    """docstring for DepFormatter"""
    def __init__(self, parser):
        super().__init__()
        self.parser = parser

    def drawDepfileTree(self):
        t = Tree(self.parser.depfile.name)
        self._drawLeaves(self.parser.depfile, t)
        return t


    def _drawLeaves(self, depfile, tree):
        for c in depfile.children:
            branch = tree.add(
                f"📄 {c.name}" 
                + (f" [red]errors: {len(c.errors)}[/red]" if c.errors else "") 
                + (f" [red]unresolved: {len(c.unresolved)}[/red]" if c.unresolved else "")
            )
            self._drawLeaves(c, branch)

    def _drawPackages(self, aPkgs):
        if not aPkgs:
            return ''

        return  Panel(' '.join(list(aPkgs)))

    def drawPackages(self):
        """
        Draws the list of packages
        """
        return self._drawPackages(self.parser.packages)

    def drawUnresolvedPackages(self):
        """
        Draws the list of unresolved packages
        """
        return self._drawPackages(self.parser.unresolvedPackages)

    def _drawComponents(self, aPkgs):
        if not aPkgs:
            return Panel.fit('')

        lString = ''
        for pkg in sorted(aPkgs):
            lString += '+ %s (%d)\n' % (pkg, len(aPkgs[pkg]))
            lSortCmps = sorted(aPkgs[pkg])
            for cmp in lSortCmps[:-1]:
                lString += u'  ├──' + str(cmp) + '\n'
            lString += u'  └──' + str(lSortCmps[-1]) + '\n'

        return Panel.fit(lString[:-1])

    def drawComponents(self):
        """
        Draws the component tree
        """
        return self._drawComponents(self.parser.packages)

    def drawUnresolvedComponents(self):
        """
        Draws the unresolved component tree
        """
        return self._drawComponents(self.parser.unresolvedComponents)

    def drawDeptreeCommandsSummary(self):
        """
        Draws a deptree commands summary table.
        
        """

        lDepTable = Table( *dep_command_types)
        lDepTable.add_row( *(str(len(self.parser.commands[k])) for k in dep_command_types) )
        return lDepTable


    def drawUnresolvedSummary(self):
        """
        Draws a summary table of the unresolved files by category
        """
        lParser = self.parser
        if not lParser.unresolved:
            return ''

        lUnresolved = Table("packages", "components", "paths")
        lUnresolved.add_row(
            str(len(lParser.unresolvedPackages)),
            str(len(lParser.unresolvedComponents)),
            str(len(lParser.unresolvedPaths)),
        )
        return lUnresolved

    def drawUnresolvedFiles(self):
        """
        Draws the table of unresolved files
        """
        lFNF = self.parser.unresolvedFiles
        if not lFNF:
            return ""

        lFNFTable = Table('path expression', 'package', 'component', 'included by')
        # lFNFTable.set_deco(Texttable.HEADER | Texttable.BORDER)

        for pkg in sorted(lFNF):
            lCmps = lFNF[pkg]
            for cmp in sorted(lCmps):
                lPathExps = lCmps[cmp]
                for pathexp in sorted(lPathExps):
                    lFNFTable.add_row(
                        relpath(pathexp, self.parser.rootdir),
                        pkg,
                        cmp,
                        '\n'.join(
                            [(relpath(src, self.parser.rootdir) if src != '__top__' else '(top)') for src in lPathExps[pathexp]]
                        ),
                    )
        return lFNFTable

    def drawParsingErrors(self):
        """
        Draws a text table detailing parsing errors.
        
        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """

        lErrors = self.parser.errors

        lErrTable = Table('dep file', 'line', 'error')

        for lPkg, lCmp, lDepName, lDepPath, lLineNo, lLine, lErr in lErrors:
            
            lErrTable.add_row(
                    relpath(lDepPath, self.parser.rootdir)+':'+str(lLineNo),
                    "'"+lLine+"'",
                    str(lErr)+(': {}'.format(lErr.__cause__) if hasattr(lErr,'__cause__') else ''),
            )

        return lErrTable

    # -----------------------------------------------------------------------------
    def drawSummary(self):

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_row("[bold]Groups[/]")
        grid.add_row(self.drawDeptreeCommandsSummary())
        grid.add_row("")
        grid.add_row("[bold]Packages[/]")
        grid.add_row(self.drawPackages())
        grid.add_row("")
        if self.parser.unresolved:
            grid.add_row("[bold]Unresolved[/]")
            grid.add_row(self.drawUnresolvedSummary())

        # Switch to using tables
        # lOutTxt = ''
        # lOutTxt += self.drawDeptreeCommandsSummary()

        # lOutTxt += '\n'
        # lOutTxt += self.drawPackages()

        # if self.parser.unresolved:
        #     lOutTxt += self.drawUnresolvedSummary()
        #     return lOutTxt

        return grid

    # -----------------------------------------------------------------------------
    def drawErrorsTable(self):
        lErrsTable = Table.grid(Column('error_tables'))

        if self.parser.errors:
            t = self.drawParsingErrors()
            t.title = "Dep tree parsing error(s)"
            t.title_style = 'bold red'
            t.title_justify = 'left'
            lErrsTable.add_row(t)

        if self.parser.unresolved:
            if self.parser.unresolvedPackages:
                t = self.drawUnresolvedPackages()
                t.title = "[bold red]Unresolved packages[/bold red]"
                lErrsTable.add_row(t)
            # ------
            lCNF = self.parser.unresolvedComponents
            if lCNF:
                t = self.drawUnresolvedComponents()
                t.title = "[bold red]Unresolved components[/bold red]"
                lErrsTable.add_row(t)


        if self.parser.unresolvedFiles:
            t = self.drawUnresolvedFiles()
            t.title = "Unresolved files"
            t.title_style = 'bold red'
            t.title_justify = 'left'
            lErrsTable.add_row(t)

        return lErrsTable

    def hasErrors(self):
        return self.parser.errors or self.parser.unresolved or self.parser.unresolvedFiles