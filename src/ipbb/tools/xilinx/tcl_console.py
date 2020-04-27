from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------


# -------------------------------------------------------------------------
def generate_console_context(aTCLConsoleClass):
    
    class ConsoleCtxClass(object):
        """VivadoConsole wrapper for with statements
        """

        # --------------------------------------------------------------
        def __getattr__(self, name):
            if name.startswith('_'):
                # bail out early
                raise AttributeError(name)
            return getattr(self._console, name)

        # --------------------------------------------------------------
        def __setattr__(self, name, value):
            if name.startswith('_'):
                self.__dict__[name] = value
                return
            return setattr(self._console, name, value)

        # --------------------------------------------------------------
        def __init__(self, *args, **kwargs):
            super(ConsoleCtxClass, self).__init__()
            self._args = args
            self._kwargs = kwargs

        # --------------------------------------------------------------
        def __enter__(self):
            self._console = aTCLConsoleClass(*self._args, **self._kwargs)
            return self

        # --------------------------------------------------------------
        def __exit__(self, type, value, traceback):
            self._console.quit()

        # --------------------------------------------------------------
        def __call__(self, aCmd=None, aMaxLen=1):
            # FIXME: only needed because of VivadoProjectMaker
            # Fix at source and remove
            if aCmd is None:
                return

            if aCmd.count('\n') is not 0:
                aCmd = aCmd.split('\n')

            if isinstance(aCmd, str):
                return self._console.execute(aCmd, aMaxLen)
            elif isinstance(aCmd, list):
                return self._console.executeMany(aCmd, aMaxLen)
            else:
                raise TypeError('Unsupported command type ' + type(aCmd).__name__)
    return ConsoleCtxClass



# -------------------------------------------------------------------------
class TCLConsoleSnoozer(object):
    """Snoozes notifications from Vivado """
    # --------------------------------------------------------------
    def __init__(self, aConsole):
        super(ConsoleSnoozer, self).__init__()
        self._console = aConsole
        self._quiet = None
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __enter__(self):
        self._quiet = self._console.quiet
        self._console.quiet = True
    # --------------------------------------------------------------

    # --------------------------------------------------------------
    def __exit__(self, type, value, traceback):
        self._console.quiet = self._quiet
    # --------------------------------------------------------------
