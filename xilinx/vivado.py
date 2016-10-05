# from ipopen import IPopen, AppHandler

# class VivadoHandler(AppHandler):
#     """docstring for VivadoHandler"""

#     enterFmt='ENTER - {0}'
#     exitFmt='EXIT - {0}'

#     def __init__(self):
#         super(VivadoHandler, self).__init__()
#         self.hash = hashlib.sha1()

#     @staticmethod
#     def _echo(ipopen, text):
#         # 
#         ipopen._send('puts "{0}"'.format(text))

#     def enter(self, ipopen):
#         # Update hash
#         self.hash.update(str(time.time()))

#         # update tokens
#         self.enterToken = self.enterFmt.format(self.hash.hexdigest())
#         self.exitToken = self.exitFmt.format(self.hash.hexdigest())
        
#         # Inject a start token (not used)
#         self._echo(ipopen, self.enterToken)

#     def exit(self, ipopen):
#         # inject end token
#         self._echo(ipopen, self.exitToken)

#     def finished(self, output_buffer):
#         # Search for end token
#         return output_buffer.endswith(self.exitToken+'\n')

#     def trim(self, output_buffer):
#         index = output_buffer.find(self.enterToken+'\n')
#         return output_buffer[index+len(self.enterToken)+1:-(len(self.exitToken)+1)]

# class Vivado:
#     def __init__(self):
#         cmd = 'vivado -mode tcl'
#         self._me = IPopen(cmd.split(),verbose=True, handler=VivadoHandler())

#         def echo(self, text):
#             return 'puts "{0}"'.format(text)

#         # self._me.echo = echo

#     def __del__(self):
#         self._me.communicate()

#     def execute(self, *args, **kwargs):
#         return self._me.execute(*args,**kwargs)

#     def run(self, *args, **kwargs):
#         return self._me.run(*args,**kwargs)

#     def openHw(self):
#         self.execute('open_hw')

#     def connect(self,uri):
        # return self._me.execute('connect_hw_server -url %s',uri)

import logging
import pexpect

class Vivado(object):
    """docstring for Vivado2"""
    def __init__(self):
        super(Vivado, self).__init__()
        self._log = logging.getLogger('Vivado')
        self._log.debug('Starting Vivado')
        self._me = pexpect.spawn('vivado -mode tcl')
        self.__expectprompt()
        self._log.debug('Vivado up and running')

        # print self._me.before

    def __del__(self):
        self.execute('quit')
        self._me.close()

    def __expectprompt(self):
        index = None
        buffer = []
        while True:
            # Search for newlines, prompt, end-of-file
            index = self._me.expect(['\r\n','Vivado%\t', pexpect.EOF])
            print '>',self._me.before

            # Break if prompt or EOF
            if index != 0:
                break

            # Store the 
            buffer += [self._me.before]

        return buffer

    def __send(self, text):
        self._me.sendline(text)

    def execute(self, text):

        import re
        char_backspace = re.compile(".\b")
        
        self.__send(text)
        output = self.__expectprompt()

        # sanitise Vivado output (backspaces leaking in here?!?)
        cmdrcvd = char_backspace.sub('',output[0])
        cmdsent = text
        if cmdrcvd != cmdsent:
            print len(cmdrcvd), len(cmdsent)
            for i in xrange(min(len(cmdrcvd), len(cmdsent))):
                r = cmdrcvd[i]
                s = cmdsent[i]
                # print i, '\t', r, ord(r), ord(r) > 128, '\t', s, ord(s), ord(s) > 128 
                print i, '\t', r, s, r==s, ord(r)

            print ''.join([str(i%10) for i in xrange(len(cmdrcvd))])
            print cmdrcvd
            print ''.join([str(i%10) for i in xrange(len(cmdsent))])
            print cmdsent

            raise RuntimeError('Command and first output line don\'t match cmdsent=\'{0}\', cmdrcvd=\'{1}\''.format(cmdsent,cmdrcvd))
        return output[1:]

    def openHw(self):
        return self.execute('open_hw')
        
    def connect(self,uri):
        return self.execute('connect_hw_server -url %s' % uri)

    def getHwTargets(self):
        return self.execute('get_hw_targets')[0].split()

    def openHwTarget(self, target):
        return self.execute('open_hw_target {{{0}}}'.format(target))

    def getHwDevices(self):
        return self.execute('get_hw_devices')[0].split()

    # def setCurrentHwDevice(self, device):
        # return self.execute('current_hw_device {0}'.format(device))

    def programDevice(self, device, bitfile):
        from os.path import abspath, normpath

        bitpath = abspath(normpath(bitfile))

        self._log.debug('Programming %s with %s',device, bitfile)

        self.execute('current_hw_device {0}'.format(device))
        self.execute('refresh_hw_device -update_hw_probes false [current_hw_device]')
        self.execute('set_property PROBES.FILE {{}} [current_hw_device]')
        self.execute('set_property PROGRAM.FILE {{{0}}} [current_hw_device]'.format(bitpath))
        self.execute('program_hw_devices [current_hw_device]')

