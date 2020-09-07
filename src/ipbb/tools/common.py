from __future__ import print_function, absolute_import
from past.builtins import basestring
# -------------------------------------------------------------------------

import os
import sys
import pexpect
import subprocess
import time

from locale import getpreferredencoding

DEFAULT_ENCODING = getpreferredencoding() or "UTF-8"

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

    def __init__(self, prefix=None, sep='', quiet=False):
        self._write = sys.stdout.write
        self._flush = sys.stdout.flush
        self.quiet = quiet
        self._prefix = prefix
        self._sep = sep
        self._pending = False
        # update prefixstr
        self._update()

    def __del__(self):
        pass

    def __enter__(self):
        pass

    def __exit__(self, *args):
        pass


    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def prefix(self, value):
        self._prefix = value
        self._update()

    @property
    def sep(self):
        return self._sep

    @sep.setter
    def sep(self, value):
        self._sep = value
        self._update()

    def _update(self):
        self._prefixstr =  (self._prefix + self._sep) if self._prefix is not None else ''

    def write(self, message):
        """
        Arguments:
            message (string): Input message

        Returns:
            string: Formatted message

        """
        if self.quiet:
            return

        msg = (self.prefix + self.sep) if (self._pending and self.prefix) else ''

        # update _pending status
        self._pending = message.endswith('\n')

        # furthemore, postfix the prefix to the newlines in message, execpt for the last one if pending is pn
        msg += (
            message.replace(
                '\n', '\n' + (self.prefix + self.sep), message.count('\n') - self._pending
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
def mkdir(path, mode=0o777):
    try:
        os.makedirs(path, mode)
    except OSError:
        if os.path.exists(path) and os.path.isdir(path):
            return
        raise
