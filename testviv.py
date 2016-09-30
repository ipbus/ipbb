#!/usr/bin/env python
#
import subprocess
import sys

process = subprocess.Popen(
    'vivado -mode tcl'.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE
)
print 'stica'
while True:
    out = process.stdout.read(1)
    if out == '' and process.poll() != None:
        break
    if out != '':
        sys.stdout.write(out)
        sys.stdout.flush()
        
#

# import hw.vivado


# viv = hw.vivado.Vivado()
# viv.execute('')



# class IPopen(subprocess.Popen):

#     POLL_INTERVAL = 0.1
#     def __init__(self, *args, **kwargs):
#         subprocess.Popen.__init__(self,
#             ['vivado','-mode','tcl'], 
#             # ['gdb'], 
#             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
#             )
#         while True:
#             out = self.stdout.read(1)
#             if out == '' and self.poll() != None:
#                 break
#             if out != '':
#                 sys.stdout.write(out)
#                 sys.stdout.flush()

# if __name__ == '__main__':
#     x = IPopen()