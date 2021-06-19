
import os
import sys
import pexpect
import subprocess
import time


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

