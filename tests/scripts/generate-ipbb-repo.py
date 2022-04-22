#!/usr/bin/env python3

import click
import traceback
import yaml
import pprint
from click import echo, secho
from rich.panel import Panel
from rich.text import Text
from os.path import exists, dirname, join, basename, splitext
from os import mkdir, makedirs
from shutil import rmtree
from ipbb.depparser import DepFileParser, DepFormatter
from ipbb.depparser import Pathmaker
from ipbb.console import cprint, console
from rich.table import Table, Column

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command('cli', context_settings=CONTEXT_SETTINGS)
@click.argument('repofile', type=click.Path(exists=True))
@click.argument('dest', type=click.Path())
def cli(repofile, dest):

    with open(repofile, 'r') as f:
        repocfg = yaml.safe_load(f)
    cprint(Panel.fit("Repo config"))
    cprint(repocfg)

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

    pm = Pathmaker( repopath if repocfg.get('multi_pkg', False) else dest )

    for t in repocfg['top']:
        cmp = t['cmp']
        pkg = t['pkg'] if 'pkg' in t else reponame


        cprint("Parsing", t)
        dp = DepFileParser('vivado', pm, {}, 0)
        # import ipdb
        # ipdb.set_trace()
        dp.parse(pkg, t['cmp'], t['file'])

        cprint('\n')
        cprint('-'*80)
        cprint('   Summary   ', t['file'])
        cprint('-'*80)
        cprint(">>> Commands")
        cprint(dp.commands)
        cprint(">>> Libs")
        cprint(dp.libs)
        cprint(">>> Errors")
        cprint(dp.errors)
        cprint(">>> Lost files")
        cprint(dp.unresolved)

        df = DepFormatter(dp)
        cprint(Panel.fit(df.draw_summary()))

        cprint(Panel.fit(df.draw_error_table(), title='[bold red]dep tree errors[/bold red]'))


def main():
    try:
        cli()
    except Exception as e:
        console.print_exception()
        raise SystemExit(-1)


if __name__ == '__main__':
    main()
