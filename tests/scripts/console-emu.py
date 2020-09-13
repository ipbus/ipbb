#!/usr/bin/env python

import click

from cmd import Cmd


banner_map = {
    # Vivado:
    'vivado': '''
Vivado v2017.4 (64-bit)
SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
IP Build 2085800 on Fri Dec 15 22:25:07 MST 2017
Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.
''',
    # VivadoLab:
    'vivadolab': '''
Vivado Lab Edition v2017.4 (64-bit)
SW Build 2086221 on Fri Dec 15 20:54:30 MST 2017
Copyright 1986-2017 Xilinx, Inc. All Rights Reserved.
'''
}

prompt_map = {
    'vivado': r'Vivado% ',
    'vivadolab': r'VivadoLab% '
}

class ConsoleEmulator(Cmd, object):

    def __init__(self, mode):
        # print('xxx')
        super(ConsoleEmulator, self).__init__()
        self.intro = banner_map.get(mode, "no banner")
        self.prompt = prompt_map.get(mode, 'no prompt> ')

 
    def do_quit(self, inp):
        print(inp)
        print("Quitting")
        return True
    
    def default(self, inp):
        # if inp == 'x' or inp == 'q':
        #     return self.do_exit(inp)
 
        print("Received command: {}".format(inp))
 
    do_exit = do_quit
    do_EOF = do_quit
 

# @click.command()
# @click.argument('mode', type=click.Choice(['vivado']))
# def cli(mode):
#     """Simple console emulator."""
#     ConsoleEmulator(mode).cmdloop()

if __name__ == '__main__':
    ConsoleEmulator('vivado').cmdloop()
    