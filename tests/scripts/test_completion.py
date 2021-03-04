#!/usr/bin/env python


import sys
import click

from ipbb.scripts.builder import climain, _compose_cli
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def main():
    '''Discovers the env at startup'''

    if sys.version_info[0:2] < (2, 7):
        click.secho("Error: Python 2.7 is required to run IPBB", fg='red')
        raise SystemExit(-1)

    _compose_cli()

    from click._bashcomplete import get_choices

    def choices_without_help(cli, args, incomplete):
        completions = get_choices(cli, 'dummy', args, incomplete)
        return [c[0] for c in completions]

    for inc in [
            '',
            'f',
            'felix-pie',
            'felix-pie:',
            'felix-pie:p',
            'felix-pie:projects/',
            'felix-pie:projects/hi',
            'felix-pie:projects/hitfinder/'
    ]:
        print("-" * 80)
        print("Completing component'" + inc + "'")
        print("-" * 80)
        print(choices_without_help(climain, ['proj', 'create', 'vivado', 'jbsc-hf-fc-tightG'], inc))
        print()

    for inc in [
            '',
    ]:
        print("-" * 80)
        print("Completing dep file'" + inc + "'")
        print("-" * 80)
        print(choices_without_help(climain, ['ipbb', 'toolbox', 'check-dep', 'felix-pie:projects/hitfinder'], inc))
        print()

    for inc in [
            '',
    ]:
        print("-" * 80)
        print("Completing dep file'" + inc + "'")
        print("-" * 80)
        print(choices_without_help(climain, ['proj', 'create', 'vivado', 'jbsc-hf-fc-tightG', 'felix-pie:projects/hitfinder', '-t'], inc))
        print()
    raise SystemExit(0)

if __name__ == '__main__':
    main()