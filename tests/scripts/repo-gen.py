#!/usr/bin/env python
from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems

import click
import traceback
import yaml
import pprint
from click import echo, secho
from os.path import exists, dirname, join
from os import mkdir, makedirs
from shutil import rmtree

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('cli', context_settings=CONTEXT_SETTINGS)
@click.argument('cfg', type=click.Path(exists=True))
@click.argument('dest', type=click.Path())
def cli(cfg, dest):
    print(cfg, dest)
    with open(cfg, 'r') as f:
        x = yaml.safe_load(f)
    pprint.pprint(x)

    if exists(dest):
        rmtree(dest)

    mkdir(dest)

    for p, t in iteritems(x['files']):
        d = join(dest, dirname(p))
        if not exists(d):
            makedirs(d)

        with open(join(dest, p), 'w') as f:
            f.write(t)



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
