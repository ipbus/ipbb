from __future__ import print_function

# -------------------------------------------------------------------------

import os
import sys
import pexpect
import subprocess
import time


# ------------------------------------------------------------------------------
class SmartOpen(object):

    # -------------------------------------------
    def __init__(self, aTarget):
        if isinstance(aTarget, basestring):
            self.target = open(aTarget, 'w')
        elif aTarget is None:
            self.target = sys.stdout
        else:
            self.target = aTarget

    # -------------------------------------------
    @property
    def path(self):
        if self.target is not sys.stdout:
            return self.target.name
        else:
            return None

    # -------------------------------------------
    def __enter__(self):
        return self

    # -------------------------------------------
    def __exit__(self, type, value, traceback):
        if self.target is not sys.stdout:
            self.target.close()

    # -------------------------------------------
    def __call__(self, *strings):
        self.target.write(' '.join(strings))
        self.target.write("\n")
        self.target.flush()

    # -------------------------------------------


# ------------------------------------------------------------------------------
class OutputFormatter(object):
    """
    Output formatter class

    Attributes:
        prefix (str): String to be prepent to each output line.
        quiet (bool): Suppress output.
    """

    def __init__(self, prefix=None, quiet=False):
        self._write = sys.stdout.write
        self._flush = sys.stdout.flush
        self.quiet = quiet
        self.prefix = prefix
        self.pending = False

    def __del__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass

    def write(self, message):
        """
        Arguments:
            message (string): Input message

        Returns:
            string: Formatted message

        """
        if self.quiet:
            return

        msg = self.prefix if (self.pending and self.prefix) else ''

        # update pending status
        self.pending = message.endswith('\n')

        # furthemore, postfix the prefix to the newlines in message, execpt for the last one if pending is pn
        msg += (
            message.replace(
                '\n', '\n' + self.prefix, message.count('\n') - self.pending
            )
            if self.prefix
            else message
        )

        self._write(msg)

    def flush(self):
        """Flushes the internal buffer

        """
        if self.quiet:
            return
        self._flush()


# ------------------------------------------------------------------------------
# Helper function equivalent to which in posix systems
def which(aExecutable):
    '''Searches for exectable il $PATH'''
    lSearchPaths = (
        os.environ["PATH"].split(os.pathsep)
        if aExecutable[0] != os.sep
        else [os.path.dirname(aExecutable)]
    )
    for lPath in lSearchPaths:
        if not os.access(os.path.join(lPath, aExecutable), os.X_OK):
            continue
        return os.path.normpath(os.path.join(lPath, aExecutable))
    return None


# ------------------------------------------------------------------------------
def mkdir(path, mode=0777):
    try:
        os.makedirs(path, mode)
    except OSError:
        if os.path.exists(path) and os.path.isdir(path):
            pass
        return
