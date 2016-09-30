from . import IPopen

class Vivado:
    def __init__(self):
        cmd = 'vivado -mode tcl'
        self._me = IPopen(cmd.split())

    def __del__(self):
        self._me.communicate()

    def exec(self, *args, **kwargs):
        self._me.exec(*args,**kwargs)

    def run(self, *args, **kwargs):
        self._me.run(*args,**kwargs)

    def openHw(self):
        self.exec('open_hw')

    def connect(self,uri):
        self._me.execute('connect_hw_server -url %s',uri)