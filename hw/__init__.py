import os
import time
import fcntl
import subprocess
import hashlib
import time

class AppHandler(object):
    """docstring for AppHandler"""
    def __init__(self):
        super(AppHandler, self).__init__()

    def enter(self, ipopen):
        raise RuntimeError('enter: Not implemented')

    def exit(self, ipopen):
        raise RuntimeError('exit: Not implemented')

    def finished(self, output_buffer):
        raise RuntimeError('finished: Not implemented')

    def trim(self, output_buffer):
        raise RuntimeError('finished: Not implemented')

class PromptHandler(AppHandler):
    """docstring for PromptHandler"""
    def __init__(self, prompt):
        super(PromptHandler, self).__init__()
        self.prompt = prompt

    def enter(self, ipopen):
        pass
        
    def exit(self, ipopen):
        pass

    def finished(self, output_buffer):
        return output_buffer.endswith(self.prompt)

    def trim(self, output_buffer):
        return output_buffer


class IPopen(subprocess.Popen):

    POLL_INTERVAL = 0.1
    def __init__(self, *args, **kwargs):
        """Construct interactive Popen."""
        keyword_args = {
            'stdin': subprocess.PIPE,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'handler': PromptHandler('>'),
            'verbose': False
        }
        keyword_args.update(kwargs)
        self.handler = keyword_args.get('handler')
        del keyword_args['handler']
        self.verbose = keyword_args.get('verbose')
        del keyword_args['verbose']
        subprocess.Popen.__init__(self, *args, **keyword_args)
        # Make stderr and stdout non-blocking.
        for outfile in (self.stdout, self.stderr):
            if outfile is not None:
                fd = outfile.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        # Experimental
        # self.hash = hashlib.sha1()

    def __correspond(self, text, sleep=POLL_INTERVAL):
        """Communicate with the child process without closing stdin."""
        self.handler.enter(self)

        self._send(text)
        
        self.handler.exit(self)

        str_buffer = ''
        while not self.handler.finished(str_buffer):
            try:
                tmp = self.stdout.read()
                if self.verbose: print tmp
                str_buffer += tmp

            except IOError:
                time.sleep(sleep)

        return self.handler.trim(str_buffer)

    def _send(self, text):
        if self.verbose: print 'sending: '+text
        if text:
            if text[-1] != '\n': text += '\n'
        else:
            text='\n'
        self.stdin.write(text)
        self.stdin.flush()

    execute = __correspond

    def run(self, script, sleep=0.1):
        output_buffer=''
        for l in script.split('\n'):
            # print 'cmd:',l
            if not l.strip(): continue
            print "[run] "+l
            output_buffer += self._me.correspond(l, sleep)
        return output_buffer
