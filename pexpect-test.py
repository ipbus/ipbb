#!/usr/bin/env python
#
# import subprocess
# import sys, pty
# import os

# from xilinx.vivado import Vivado

# viv = Vivado(verbose=True)
# # print '-'*40
# print viv.openHw()
# # print '-'*40
# # print viv.connect('localhost:3121')
# print viv.execute('connect_hw_server -url localhost:3121')
# import time
# time.sleep(2)
# print viv.getHwTargets()


# master, slave = pty.openpty()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # p = subprocess.Popen('vivado -mode tcl'.split(),
# #     stdin=subprocess.PIPE,
# #     stdout=subprocess.PIPE,
# #     stderr=subprocess.PIPE,
# #     close_fds=True)
# p = subprocess.Popen('vivado -mode tcl'.split(),
#     stdin=master,
#     stdout=slave,
#     # stdin=os.fdopen(slave,'w'),
#     # stdout=os.fdopen(slave,'r'),
#     # stderr=os.fdopen(master,'r'),
#     close_fds=True)
# os.close(slave)
# print p.communicate('puts "Hellow World"; quit')

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# import pexpect
# child = pexpect.spawn('vivado -mode tcl')
# child.expect('Vivado%\t')
# child.sendline('puts "aaa"')
# child.expect('Vivado%\t')
# child.sendline('open_hw')
# child.expect('Vivado%\t')
# print child.before.split('\r\n')[:-1]
# child.sendline('connect_hw_server -url localhost:3121')
# child.expect('Vivado%\t')
# child.sendline('puts [get_hw_targets]')
# child.expect('Vivado%\t')
# print child.before.split('\r\n')[:-1]

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# def runPopen():
# # print timeit.timeit("
#     import subprocess
#     p=subprocess.Popen(['dummy_exe.py']); 
#     p.wait()

# def runPexpect():
#     import pexpect
#     import sys
#     s = pexpect.spawn('dummy_exe.py',logfile=sys.stdout)
#     while True:
#         index = s.expect(['\r\n',pexpect.EOF])
#         if index != 0:
#             break

# import timeit



# print '>>>>>',timeit.timeit('runPopen()', setup="from __main__ import runPopen", number=1)
# print '>>>>>',timeit.timeit('runPexpect()', setup="from __main__ import runPexpect", number=1)
