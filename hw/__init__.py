import os
import time
import fcntl
import subprocess


class IPopen(subprocess.Popen):

    POLL_INTERVAL = 0.1
    def __init__(self, *args, **kwargs):
        """Construct interactive Popen."""
        keyword_args = {
            'stdin': subprocess.PIPE,
            'stdout': subprocess.PIPE,
            'stderr': subprocess.PIPE,
            'prompt': '>',
            'verbose': False
        }
        keyword_args.update(kwargs)
        self.prompt = keyword_args.get('prompt')
        del keyword_args['prompt']
        self.verbose = keyword_args.get('verbose')
        del keyword_args['verbose']
        subprocess.Popen.__init__(self, *args, **keyword_args)
        # Make stderr and stdout non-blocking.
        for outfile in (self.stdout, self.stderr):
            if outfile is not None:
                fd = outfile.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    def __correspond(self, text, sleep=0.1):
        """Communicate with the child process without closing stdin."""
        if text:
            if text[-1] != '\n': text += '\n'
        else:
            text='\n'
        self.stdin.write(text)
        self.stdin.flush()
        str_buffer = ''
        while not str_buffer.endswith(self.prompt):
            try:
                tmp = self.stdout.read()
                if self.verbose: print tmp
                str_buffer += tmp 
            except IOError:
                time.sleep(sleep)

        return str_buffer

    exec = __run

    def run(self, script, sleep=0.1):
        output_buffer=''
        for l in script.split('\n'):
            # print 'cmd:',l
            if not l.strip(): continue
            print "[run] "+l
            output_buffer += self._me.correspond(l, sleep)
        return output_buffer