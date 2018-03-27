
import click

from click import echo, style, secho
from os.path import basename, relpath
import re
from texttable import Texttable

from ..depparser.Pathmaker import Pathmaker
from ..depparser.DepFileParser import DepFileParser



# ------------------------------------------------------------------------------
def _validateComponent(ctx, param, value):
    lSeparators = value.count(':')
    # Validate the format
    if lSeparators != 1:
        raise click.BadParameter('Malformed component name : %s. Expected <package>:<component>' % value)

    return tuple(value.split(':'))
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@click.group('toolbox', short_help="Miscelaneous useful commands.")
@click.pass_obj
def toolbox(env):
    '''Miscelaneous useful commands'''
    # -------------------------------------------------------------------------
    # Must be in a build area
    if env.work.path is None:
        raise click.ClickException('Build area root directory not found')
    # -------------------------------------------------------------------------
# ------------------------------------------------------------------------------


@toolbox.command('check-dep-files', short_help="Performs basic checks on dependency files")
@click.option('-v', '--verbose', count=True)
@click.argument('component', callback=_validateComponent)
@click.argument('depfile', required=False, default=None)
@click.option('-t', '--toolset', required=True, type=click.Choice(['vivado','sim']))
@click.pass_obj
def check_dep_files(env, verbose, component, depfile, toolset):
    '''Perform basic checks on dependency files'''

    lPackage, lComponent = component
    if depfile is None:
        depfile = basename(lComponent) + ".dep"

    lPathMaker = Pathmaker(env.srcdir, env._verbosity)
    lParser = DepFileParser(toolset, lPathMaker)
    lParser.parse(lPackage, lComponent, depfile)

    echo ()

    ### N.B. Rest of this function is heavily based on implementation of 'dep report' command; assuming
    ###   that output of these 2 commands does not significantly diverge, might make sense to implement
    ###   command output in a separate function, that's invoked by both commands

    lCmdHeaders = ['path', 'flags', 'map', 'lib'] # ['path', 'flags', 'package', 'component', 'map', 'lib']
    lFilters = []

    lPrepend = re.compile('(^|\n)')
    if verbose:
        secho('Parsed commands', fg='blue')

        for k in lParser.commands:
            echo( '  + {0} ({1})' .format(k, len(lParser.commands[k])) )
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
                    #lCmd.Package,
                    #lCmd.Component,
                    lCmd.Map,
                    lCmd.Lib,

                ]

                if lFilters and not all([ rxp.match(lRow[i]) for i,rxp in lFilters ]):
                    continue
                    
                lCmdTable.add_row(lRow)           

            echo(lPrepend.sub('\g<1>    ',lCmdTable.draw()))
            echo()

        secho('Resolved packages & components', fg='blue')

        string = ''
        for pkg in sorted(lParser.components):
            string += '  + %s (%d)\n' % (pkg, len(lParser.components[pkg]))
            for cmp in sorted(lParser.components[pkg]):
                string += '    > ' + str(cmp) + '\n'
        echo(string)


    if lParser.missingPackages:
        secho ('Missing packages:', fg='red')
        echo(str(list(lParser.missingPackages)))


    lCNF = lParser.missingComponents
    if lCNF:
        secho ('Missing components:', fg='red')
        string = ''

        for pkg in sorted(lCNF):
            string += '+ %s (%d)\n' % (pkg, len(lCNF[pkg]))

            for cmp in sorted(lCNF[pkg]):
                string += '  > ' + str(cmp) + '\n'
        echo(string)

        
    lFNF = lParser.missingFiles
    if lFNF:
        secho ('Missing files:', fg='red')

        lFNFTable = Texttable(max_width=0)
        lFNFTable.header(['path','included by']) # ['path expression','package','component','included by'])
        lFNFTable.set_deco(Texttable.HEADER | Texttable.BORDER)

        for pkg in sorted(lFNF):
            lCmps = lFNF[pkg]
            for cmp in sorted(lCmps):
                lPathExps = lCmps[cmp]
                for pathexp in sorted(lPathExps):

                    lFNFTable.add_row([
                        relpath(pathexp, env.srcdir),
                        #pkg,
                        #cmp,
                        '\n'.join([relpath(src, env.srcdir) for src in lPathExps[pathexp]]),
                        ])
        echo(lPrepend.sub('\g<1>  ',lFNFTable.draw()))
        echo()


    if lParser.missingPackages or lParser.missingComponents or lParser.missingFiles:
        raise click.ClickException("Cannot find 1 or more files referenced by depfile {}".format(lPathMaker.getPath(lPackage, lComponent, 'include', depfile)))
    elif not verbose:
        echo ("No errors found in depfile {}".format(lPathMaker.getPath(lPackage, lComponent, 'include', depfile)))


