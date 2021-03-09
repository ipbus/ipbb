#!/usr/bin/env python3

import click
import traceback
import yaml
import pprint
from click import echo, secho
from os.path import exists, dirname, join, basename, splitext
from os import mkdir, makedirs
from shutil import rmtree
from ipbb.depparser import DepFileParser, DepFormatter
from ipbb.depparser import Pathmaker

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

    for d, fs in repocfg['files'].items():
        ad = join(repopath, d)
        if not exists(ad):
            makedirs(ad)

        for f, t in fs.items():
            with open(join(ad, f), 'w') as f:
                f.write(t)

    pm = Pathmaker(dest)

    for t in repocfg['top']:
        print('++++++++++++++++++++++++ Parsing',t, '+++++++++')
        dp = DepFileParser('vivado', pm, {}, 0)
        # import ipdb
        # ipdb.set_trace()
        dp.parse(reponame, t['cmp'], t['file'])

        print('\n\n\n')
        print('-'*80)
        print('   Summary   ', t['file'])
        print('-'*80)
        print(">>> Commands")
        pprint.pprint(dp.commands)
        print(">>> Libs")
        pprint.pprint(dp.libs)
        print(">>> Errors")
        pprint.pprint(dp.errors)
        print(">>> Lost files")
        pprint.pprint(dp.unresolved)

        df = DepFormatter(dp)
        print(df.drawSummary())


def main():
    try:
        cli()
    except Exception as e:
        hline = '-' * 80
        echo()
        secho(hline, fg='red')
        secho("FATAL ERROR: Caught '" + type(e).__name__ + "' exception:", fg='red')
        secho(e, fg='red')
        secho(hline, fg='red')
        import StringIO

        lTrace = StringIO.StringIO()
        traceback.print_exc(file=lTrace)
        print(lTrace.getvalue())
        # Do something with lTrace
        raise SystemExit(-1)


if __name__ == '__main__':
    main()
