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

import timeit



# print '>>>>>',timeit.timeit('runPopen()', setup="from __main__ import runPopen", number=1)
# print '>>>>>',timeit.timeit('runPexpect()', setup="from __main__ import runPexpect", number=1)

def runVivadoPexpect():
    from xilinx.vivado import Console
    v = Console()
    v.execute(['puts "%d"' % i for i in xrange(100)])
    del v

def runVivadoIPopen():
    from xilinx.vivado_old import Vivado

    v = Vivado()
    for i in xrange(100):
        v.execute('puts "%d"' % i, sleep=0.)

def runVivadoIPopenB():
    from xilinx.vivado_old import Vivado

    v = Vivado()
    v.execute(['puts "%d"' % i for i in xrange(100)], sleep=0.01)

def runVivadoBatch():
    import subprocess
    with open('echo.tcl','w') as tcl:
        for i in xrange(100):
            tcl.write('puts "%d"\n' % i)
    process = subprocess.Popen('vivado -mode batch -source echo.tcl'.split())
    process.communicate()

def runVivadoTempFile():
    import fcntl, os

    from subprocess import Popen, STDOUT, PIPE
    from tempfile import NamedTemporaryFile

    with NamedTemporaryFile() as f:



        p = Popen('vivado -mode batch'.split(), stdin=PIPE, stdout=f, stderr=f)
        fd = f.fileno()
        fl = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        # p.communicate()

        f.seek(0)
        output = f.readlines()
        print output

        p.stdin.write('puts "pippo"')
        p.stdin.flush()
        output = f.readlines()
        print output


def runPythonPexpect():
    import pexpect, re
    import sys

    prompt = re.compile('>>>')

    py = pexpect.spawn('python')
    py.expect_list([prompt])

    py.logfile = sys.stdout
    for i in xrange(100):
        py.sendline('print "%d"' % i)
    py.sendline('game_over')

    py.expect(['game_over'])


from ipopen import AppHandler
import hashlib, time
class PythonHandler(AppHandler):
    """docstring for VivadoHandler"""

    enterFmt='ENTER - {0}'
    exitFmt='EXIT - {0}'

    def __init__(self):
        super(PythonHandler, self).__init__()
        self.hash = hashlib.sha1()

    @staticmethod
    def _echo(ipopen, text):
        # 
        ipopen._send('print "{0}"'.format(text))

    def enter(self, ipopen):
        # Update hash
        self.hash.update(str(time.time()))

        # update tokens
        self.enterToken = self.enterFmt.format(self.hash.hexdigest())
        self.exitToken = self.exitFmt.format(self.hash.hexdigest())
        
        # Inject a start token (not used)
        self._echo(ipopen, self.enterToken)

    def exit(self, ipopen):
        # inject end token
        self._echo(ipopen, self.exitToken)

    def finished(self, output_buffer):
        # Search for end token
        return output_buffer.endswith(self.exitToken+'\n')

    def trim(self, output_buffer):
        index = output_buffer.find(self.enterToken+'\n')
        return output_buffer[index+len(self.enterToken)+1:-(len(self.exitToken)+1)]

def runPythonIPopen():
    from ipopen import IPopen, PromptHandler

    # import pdb; pdb.set_trace()
    proc = IPopen(['python'],verbose=True, handler=PythonHandler())
    proc.execute('print 0')



# runVivadoIPopen()
# t = timeit.timeit('runVivadoIPopen()', setup="from __main__ import runVivadoIPopen", number=1)
# print '>>>>> runVivadoIPopen',t

# runVivadoIPopenB()
# t = timeit.timeit('runVivadoIPopenB()', setup="from __main__ import runVivadoIPopenB", number=1)
# print '>>>>> runVivadoIPopenB',t

# runVivadoPexpect()
# t = timeit.timeit('runVivadoPexpect()', setup="from __main__ import runVivadoPexpect", number=1)
# print '>>>>> runVivadoPexpect',t

# runVivadoBatch()
# t = timeit.timeit('runVivadoBatch()', setup="from __main__ import runVivadoBatch", number=1)
# print '>>>>> runVivadoBatch',t

# runVivadoTempFile()

# runPythonIPopen()
# 
import cProfile
cProfile.run('runVivadoPexpect()')