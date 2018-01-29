from __future__ import print_function
# ------------------------------------------------------------------------------

# Modules
import click
import os
import sh
import hashlib
import collections
import contextlib
import tempfile
import sys
import re

from os.path import join, split, exists, basename, abspath, splitext, relpath, basename
from ..tools.common import which, SmartOpen
from .tools import DirSentry
from click import echo, secho, style, confirm
from texttable import Texttable


# ------------------------------------------------------------------------------
@click.group()
@click.pass_context
@click.option('-p', '--proj', default=None)
def dep(ctx, proj):
    '''Dependencies command group'''

    env = ctx.obj

    lProj = proj if proj is not None else env.project
    if lProj is not None:
        # Change directory before executing subcommand
        from .proj import cd
        ctx.invoke(cd, projname=lProj)
        return
    else:
        if env.project is None:
            raise click.ClickException('Project area not defined. Move into a project area and try again')

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_obj
@click.option('-f', '--filter', 'filters', multiple=True)
def report(env, filters):
    '''Summarise the dependency tree of the current project'''

    lCmdHeaders = ['path', 'flags', 'package', 'component', 'map', 'lib']
    
    lFilterFormat = re.compile('([^=]*)=(.*)')
    lFilterFormatErrors = []
    lFilters = []

    # print ( filters )
    
    for f in filters:
        m = lFilterFormat.match(f)
        if not m:
            lFilterFormatErrors.append(f)
        # print (m.group(1))

        try:
            i = lCmdHeaders.index(m.group(1))
            r = re.compile(m.group(2))
            lFilters.append( (i, r) )
        except RuntimeError as e:
            lFilterFormatErrors.append(f)

    if lFilterFormatErrors:
        raise click.ClickException("Filter syntax errors: "+' '.join(['\''+e+'\'' for e in lFilterFormatErrors]))
    # return
    lParser = env.depParser

    # lTitle = Texttable(max_width=0)
    # lTitle.header(['Commands'])
    # lTitle.set_chars(['-', '|', '+', '-'])
    # lTitle.set_deco(Texttable.BORDER)
    # secho(lTitle.draw(), fg='blue')

    echo()
    secho('* Parsed commands', fg='blue')

    lPrepend = re.compile('(^|\n)')
    for k in lParser.CommandList:
        echo( '  + {0} ({1})' .format(k, len(lParser.CommandList[k])) )
        if not lParser.CommandList[k]:
            echo()
            continue

        lCmdTable = Texttable(max_width=0)
        lCmdTable.header(lCmdHeaders)
        lCmdTable.set_deco(Texttable.HEADER | Texttable.BORDER)
        lCmdTable.set_chars(['-', '|', '+', '-'])
        for lCmd in lParser.CommandList[k]:
            # print(lCmd)
            # lCmdTable.add_row([str(lCmd)])
            lRow = [
                relpath(lCmd.FilePath, env.workPath),
                ','.join(lCmd.flags()),
                lCmd.Package,
                lCmd.Component,
                lCmd.Map,
                lCmd.Lib,

            ]

            if lFilters and not all([ rxp.match(lRow[i]) for i,rxp in lFilters ]):
                continue
                
            lCmdTable.add_row(lRow)           

        echo(lPrepend.sub('\g<1>  ',lCmdTable.draw()))
        echo()

    string = ''

    string += '+----------------------------------+\n'
    string += '|  Resolved packages & components  |\n'
    string += '+----------------------------------+\n'
    string += 'packages: ' + str(list(lParser.Components.iterkeys())) + '\n'
    string += 'components:\n'
    for pkg in sorted(lParser.Components):
        string += '+ %s (%d)\n' % (pkg, len(lParser.Components[pkg]))
        for cmp in sorted(lParser.Components[pkg]):
            string += '  > ' + str(cmp) + '\n'

    if lParser.NotFound:
        string += '\n'
        string += '+----------------------------------------+\n'
        string += '|  Missing packages, components & files  |\n'
        string += '+----------------------------------------+\n'

        if lParser.PackagesNotFound:
            string += 'packages: ' + \
                str(list(lParser.PackagesNotFound)) + '\n'

        # ------
        lCNF = lParser.ComponentsNotFound
        if lCNF:
            string += 'components: \n'

            for pkg in sorted(lCNF):
                string += '+ %s (%d)\n' % (pkg, len(lCNF[pkg]))

                for cmp in sorted(lCNF[pkg]):
                    string += '  > ' + str(cmp) + '\n'
        # ------

        # ------
    echo(string)
        
    lFNF = lParser.FilesNotFound

    if lFNF:

        lFNFTable = Texttable(max_width=0)
        lFNFTable.header(['path expression','package','component','included by'])
        lFNFTable.set_deco(Texttable.HEADER | Texttable.BORDER)

        for pkg in sorted(lFNF):
            lCmps = lFNF[pkg]
            for cmp in sorted(lCmps):
                lPathExps = lCmps[cmp]
                for pathexp in sorted(lPathExps):

                    lFNFTable.add_row([
                        relpath(pathexp, env.workPath),
                        pkg,
                        cmp,
                        '\n'.join([relpath(src, env.workPath) for src in lPathExps[pathexp]]),
                        ])
        echo(lPrepend.sub('\g<1>  ',lFNFTable.draw()))
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command('ls', short_help="List project files by group")
@click.argument('group', type=click.Choice(['setup', 'src', 'addrtab', 'cgpfile']))
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def ls(env, group, output):
    '''List project files by group

    - setup: Project setup scripts
    - src: Code files
    - addrtab: Address tables 
    - cgpfile: ?
    '''

    with SmartOpen(output) as lWriter:
        for addrtab in env.depParser.CommandList[group]:
            lWriter(addrtab.FilePath)
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
@dep.command('components')
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.pass_obj
def components(env, output):


    with SmartOpen(output) as lWriter:
        for lPkt, lCmps in env.depParser.Components.iteritems():
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
def hashAndUpdate(aFilePath, aChunkSize=0x10000, aUpdateHashes=None, aAlgo=hashlib.sha1):

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


@dep.command()
@click.pass_obj
@click.option('-o', '--output', default=None, help="Destination of the command output. Default: stdout")
@click.option('-v', '--verbose', count=True)
def hash(env, output, verbose):

    lAlgoName = 'sha1'

    lAlgo = getattr(hashlib, lAlgoName, None)

    # Ensure that the selecte algorithm exists
    if lAlgo is None:
        raise AttributeError(
            'Hashing algorithm {0} is not available'.format(lAlgoName)
        )

    with SmartOpen(output) as lWriter:

        if verbose:
            lTitle = "{0} hashes for project '{1}'".format(
                lAlgoName, env.project)
            lWriter("# " + '=' * len(lTitle))
            lWriter("# " + lTitle)
            lWriter("# " + "=" * len(lTitle))
            lWriter()

        lProjHash = lAlgo()
        lGrpHashes = collections.OrderedDict()
        for lGrp, lCmds in env.depParser.CommandList.iteritems():
            lGrpHash = lAlgo()
            if verbose:
                lWriter("#" + "-" * 79)
                lWriter("# " + lGrp)
                lWriter("#" + "-" * 79)
            for lCmd in lCmds:
                lCmdHash = hashAndUpdate(
                    lCmd.FilePath, aUpdateHashes=[
                        lProjHash, lGrpHash], aAlgo=lAlgo
                ).hexdigest()
                if verbose:
                    lWriter(lCmdHash, lCmd.FilePath)

            lGrpHashes[lGrp] = lGrpHash

            if verbose:
                lWriter()

        if verbose:
            lWriter("#" + "-" * 79)
            lWriter("# Per cmd-group hashes")
            lWriter("#" + "-" * 79)
            for lGrp, lHash in lGrpHashes.iteritems():
                lWriter(lHash.hexdigest(), lGrp)
            lWriter()

            lWriter("#" + "-" * 79)
            lWriter("# Global hash for project '" + env.project + "'")
            lWriter("#" + "-" * 79)
            lWriter(lProjHash.hexdigest(), env.project)

        if not verbose:
            lWriter(lProjHash.hexdigest())

    return lProjHash
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_context
def archive(ctx):
    print ('archive')

# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
@dep.command()
@click.pass_context
def ipy(ctx):
    '''Opens IPython to inspect the parser'''
    # env = ctx.obj

    import IPython
    IPython.embed()
# ------------------------------------------------------------------------------
