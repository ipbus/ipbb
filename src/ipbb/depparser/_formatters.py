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
    """Helper class to format simplify and standardize the representation of deptree data"""
    def __init__(self, parser):
        super().__init__()
        self.parser = parser


    @staticmethod
    def _format_leaf(depfile) -> str:
        return (
            f"📝 {depfile.name}", 
            f"{depfile.pkg}",
            f"{depfile.cmp}",
            f"{len(depfile.errors)}" if depfile.errors else "",
            f"{len(depfile.unresolved)}" if depfile.unresolved else ""
            )

    @staticmethod
    def _draw_leaves(depfile, tree: Tree, attrs:  Table):
        for c in depfile.children:
            label, pkg, comp, errs, unres = DepFormatter._format_leaf(c)
            
            branch = tree.add(label)
            attrs.add_row(pkg, comp, errs, unres)

            DepFormatter._draw_leaves(c, branch, attrs)

    def draw_depfile_tree(self) -> Tree:
        if not self.parser.depfile:
            return "[red]Top depfile not found[/red]"

        attrs = Table(box=None, show_header=False)
        attrs.add_column('pkg', style='cyan', justify="right", no_wrap=True)
        attrs.add_column('comp', style='cyan', no_wrap=True)
        attrs.add_column('errors', style='red', no_wrap=True)
        attrs.add_column('unresolved', style='red', no_wrap=True)

        # root node
        label, pkg, comp, errs, unres = DepFormatter._format_leaf(self.parser.depfile)
        tree = Tree(label)
        attrs.add_row(pkg, comp, errs, unres)

        # draw branches and leaves
        self._draw_leaves(self.parser.depfile, tree, attrs)

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_column()
        grid.add_row(tree, attrs)

        return grid

    def _draw_packages(self, aPkgs):
        if not aPkgs:
            return ''

        return  Panel(' '.join(list(aPkgs)))

    def draw_packages(self):
        """
        Draws the list of packages
        """
        return self._draw_packages(self.parser.packages)

    def draw_unresolved_packages(self):
        """
        Draws the list of unresolved packages
        """
        return self._draw_packages(self.parser.unresolved_packages)

    def _drawComponents(self, aPkgs):
        if not aPkgs:
            return Panel.fit('')

        lString = ''
        for pkg in sorted(aPkgs):
            lString += '📦 %s (%d)\n' % (pkg, len(aPkgs[pkg]))
            lSortCmps = sorted(aPkgs[pkg])
            for cmp in lSortCmps[:-1]:
                lString += u'  ├─ ' + str(cmp) + '\n'
            lString += u'  └─ ' + str(lSortCmps[-1]) + '\n'

        return Panel.fit(lString[:-1])

    def draw_components(self):
        """
        Draws the component tree
        """
        return self._drawComponents(self.parser.packages)

    def draw_unresolved_components(self):
        """
        Draws the unresolved component tree
        """
        return self._drawComponents(self.parser.unresolved_components)

    def draw_deptree_commands_summary(self):
        """
        Draws a deptree commands summary table.
        
        """

        lDepTable = Table( *dep_command_types)
        lDepTable.add_row( *(str(len(self.parser.commands[k])) for k in dep_command_types) )
        return lDepTable


    def draw_unresolved_summary(self):
        """
        Draws a summary table of the unresolved files by category
        """
        lParser = self.parser
        if not lParser.unresolved:
            return ''

        lUnresolved = Table("packages", "components", "paths")
        lUnresolved.add_row(
            str(len(lParser.unresolved_packages)),
            str(len(lParser.unresolved_components)),
            str(len(lParser.unresolved_paths)),
        )
        return lUnresolved

    def draw_unresolved_files(self):
        """
        Draws the table of unresolved files
        """
        lFNF = self.parser.unresolved_files
        if not lFNF:
            return ""

        lFNFTable = Table()
        lFNFTable.add_column('path expression', overflow='fold')
        lFNFTable.add_column('package', overflow='fold') 
        lFNFTable.add_column('component', overflow='fold')
        lFNFTable.add_column('included by', overflow='fold')
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

    def draw_parsing_errors(self):
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
    def draw_summary(self):

        grid = Table.grid(expand=True)
        grid.add_column()
        grid.add_row("[bold]Groups[/]")
        grid.add_row(self.draw_deptree_commands_summary())
        grid.add_row("")
        grid.add_row("[bold]Packages[/]")
        grid.add_row(self.draw_packages())
        grid.add_row("")
        if self.parser.unresolved:
            grid.add_row("[bold]Unresolved[/]")
            grid.add_row(self.draw_unresolved_summary())

        # Switch to using tables
        # lOutTxt = ''
        # lOutTxt += self.draw_deptree_commands_summary()

        # lOutTxt += '\n'
        # lOutTxt += self.draw_packages()

        # if self.parser.unresolved:
        #     lOutTxt += self.draw_unresolved_summary()
        #     return lOutTxt

        return grid

    # -----------------------------------------------------------------------------
    def draw_error_table(self):
        lErrsTable = Table.grid(Column('error_tables'))

        if self.parser.errors:
            t = self.draw_parsing_errors()
            t.title = "Dep tree parsing error(s)"
            t.title_style = 'bold red'
            t.title_justify = 'left'
            lErrsTable.add_row(t)

        if self.parser.unresolved:
            if self.parser.unresolved_packages:
                t = self.draw_unresolved_packages()
                t.title = "[bold red]Unresolved packages[/bold red]"
                lErrsTable.add_row(t)
            # ------
            lCNF = self.parser.unresolved_components
            if lCNF:
                t = self.draw_unresolved_components()
                t.title = "[bold red]Unresolved components[/bold red]"
                lErrsTable.add_row(t)


        if self.parser.unresolved_files:
            t = self.draw_unresolved_files()
            t.title = "Unresolved files"
            t.title_style = 'bold red'
            t.title_justify = 'left'
            lErrsTable.add_row(t)

        return lErrsTable

    def hasErrors(self):
        return self.parser.errors or self.parser.unresolved or self.parser.unresolved_files
