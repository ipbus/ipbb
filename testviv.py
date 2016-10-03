#!/usr/bin/env python
#
import subprocess
import sys

# process = subprocess.Popen(
    # 'bash'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
# )
# print 'stica'
# while True:
    # out = process.stdout.read(1)
    # if out == '' and process.poll() != None:
        # break
    # if out != '':
        # sys.stdout.write(out)
        # sys.stdout.flush()

#
# process = subprocess.Popen(['vivado','-mode','tcl'], shell=False,
#                            stdin=subprocess.PIPE,
#                            # stderr=subprocess.PIPE,
#                            stdout=subprocess.PIPE
#                            )

# process.stdin.write('quit\n')
# process.stdin.flush()
# print process.stdout.readline()
# # print process.stderr.readline()

# process = subprocess.Popen(['vivado','-mode','tcl'], shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=1)
# # process.stdin.write('aaa\n')
# print process.stdout.readline()
# print process.stdout.readline()
# print process.stdout.readline()
# print process.stdout.readline()
# process.stdin.write('date\n')
# print process.stdout.readline()


import hw.vivado

viv = hw.vivado.Vivado()
print '-'*40
print 'aaaa\n',viv.execute('puts "Hello, World!"')
print '-'*40
print viv.openHw()
print '-'*40



# class IPopen(subprocess.Popen):

    # POLL_INTERVAL = 0.1
    # def __init__(self, *args, **kwargs):
        # subprocess.Popen.__init__(self,
            # # ['vivado','-mode','tcl'],
            # # ['gdb'],
            # ['bash'],
            # stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            # )
        # while True:
            # out = self.stdout.read(1)
            # if out == '' and self.poll() != None:
                # break
            # if out != '':
                # sys.stdout.write(out)
                # sys.stdout.flush()

# if __name__ == '__main__':
    # x = IPopen()
