#!/usr/bin/env python
from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems

import click
import traceback
import yaml
import pprint
from click import echo, secho
from os.path import exists, dirname, join, basename, splitext
from os import mkdir, makedirs
from shutil import rmtree
from ipbb.depparser.DepParser2g import DepParser2g
from ipbb.depparser.Pathmaker import Pathmaker

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('cli', context_settings=CONTEXT_SETTINGS)
@click.argument('repofile', type=click.Path(exists=True))
@click.argument('dest', type=click.Path())
def cli(repofile, dest):
    with open(repofile, 'r') as f:
        repocfg = yaml.safe_load(f)
    pprint.pprint(repocfg)

    reponame = repocfg.get('name', splitext(basename(repofile)))
    repopath = join(dest, reponame)
    if exists(repopath):
        rmtree(repopath)

    makedirs(repopath)

    for d, fs in iteritems(repocfg['files']):
        ad = join(repopath, d)
        if not exists(ad):
            makedirs(ad)

        for f, t in iteritems(fs):
            with open(join(ad, f), 'w') as f:
                f.write(t)


    pm = Pathmaker(repopath)
    dp = DepParser2g(pm, 2)

    dp.parser


def main():
    try:
        cli()
    except Exception as e:
        hline = '-' * 80
        echo()
        secho(hline, fg='red')
        secho("FATAL ERROR: Caught '" + type(e).__name__ + "' exception:", fg='red')
        secho(e.message, fg='red')
        secho(hline, fg='red')
        import StringIO

        lTrace = StringIO.StringIO()
        traceback.print_exc(file=lTrace)
        print(lTrace.getvalue())
        # Do something with lTrace
        raise SystemExit(-1)


if __name__ == '__main__':
    main()
