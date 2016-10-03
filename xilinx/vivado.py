from ipopen import IPopen, AppHandler

class VivadoHandler(AppHandler):
    """docstring for VivadoHandler"""

    enterFmt='ENTER - {0}'
    exitFmt='EXIT - {0}'

    def __init__(self):
        super(VivadoHandler, self).__init__()
        self.hash = hashlib.sha1()

    @staticmethod
    def _echo(ipopen, text):
        # 
        ipopen._send('puts "{0}"'.format(text))

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

class Vivado:
    def __init__(self):
        cmd = 'vivado -mode tcl'
        self._me = IPopen(cmd.split(),verbose=True, handler=VivadoHandler())

        def echo(self, text):
            return 'puts "{0}"'.format(text)

        # self._me.echo = echo

    def __del__(self):
        self._me.communicate()

    def execute(self, *args, **kwargs):
        return self._me.execute(*args,**kwargs)

    def run(self, *args, **kwargs):
        return self._me.run(*args,**kwargs)

    def openHw(self):
        self.execute('open_hw')

    def connect(self,uri):
        return self._me.execute('connect_hw_server -url %s',uri)
