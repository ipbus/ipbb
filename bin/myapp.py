#!/usr/bin/env python
from click_shell import shell
import click

# @click.group()  # no longer
@shell(prompt='my-app > ', intro='Starting my app...')
def my_app():
    pass

@my_app.command()
@click.option('-v', '--verbose', count=True)
def the_command(verbose):
    print 'the_command is running (verbose =', verbose,')'

@my_app.group()
def the_group():
    pass

@click.command()
@click.option('-c','--count', default=1, help='number of greetings')
@click.argument('name')
def sub1(count, name):
    print 'sub1 is running: '+name

the_group.add_command(sub1)


if __name__ == '__main__':
    # import pdb
    # pdb.set_trace()
    my_app()