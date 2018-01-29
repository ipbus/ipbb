from __future__ import print_function
# -------------------------------------------------------------------------

import os
import sys
import pexpect
import subprocess


# ------------------------------------------------------------------------------
# Helper function equivalent to which in posix systems
def which(aExecutable):
    '''Searches for exectable il $PATH'''
    lSearchPaths = os.environ["PATH"].split(os.pathsep) if aExecutable[0] != os.sep else [os.path.dirname(aExecutable)]
    for lPath in lSearchPaths:
        if not os.access(os.path.join(lPath, aExecutable), os.X_OK):
            continue
        return os.path.normpath(os.path.join(lPath, aExecutable))
    return None
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
def mkdir(path, mode=0777):
    try:
        os.makedirs(path,mode)
    except OSError:
        if os.path.exists(path) and os.path.isdir(path):
            pass
        return
# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------
class SmartOpen(object):

    def __init__(self, aTarget):
        if isinstance(aTarget, basestring):
            self.target = open(aTarget, 'w')
        elif aTarget is None:
            self.target = sys.stdout
        else:
            self.target = aTarget

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):


        if self.target is not sys.stdout:
            self.target.close()

    def __call__(self, *strings):
        self.target.write(' '.join(strings))
        self.target.write("\n")

    def flush(self):
        self.target.flush()

    @property
    def path(self):
        if self.target is not sys.stdout:
            return self.target.name
        else:
            return None
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
class OutputFormatter(object):
    def __init__(self, prefix=None, quiet=False):
        self._write = sys.stdout.write
        self._flush = sys.stdout.flush
        self.quiet = quiet
        self.prefix = prefix

    def __del__(self):
        # self.close()
        pass

    def __enter__(self):
        pass

    def __exit__(self, *args):
        # self.close()
        pass

    def write(self, message):
        if self.quiet:
            return
        self._write(message.replace('\n', '\n' + self.prefix)
                    if self.prefix else message)

    def flush(self):
        if self.quiet:
            return
        self._flush()
# ------------------------------------------------------------------------------
