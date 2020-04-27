from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------


# -------------------------------------------------------------------------
def lazyctxmanager(aTCLConsoleClass):
    
    class LazyConsoleCtxClass(object):
        """VivadoConsole wrapper for with statements
        """

        # --------------------------------------------------------------
        def __getattr__(self, name):
            return getattr(self._console, name)

        # --------------------------------------------------------------
        def __setattr__(self, name, value):
            if name.startswith('_'):
                self.__dict__[name] = value
                return
            return setattr(self._getconsole(), name, value)

        # --------------------------------------------------------------
        def _getconsole(self):
            if self._console is None:
                self._console = aTCLConsoleClass(*self._args, **self._kwargs)
            return self._console

        # --------------------------------------------------------------
        def __init__(self, *args, **kwargs):
            super(LazyConsoleCtxClass, self).__init__()
            self._lazy = kwargs.pop('_lazy', False)
            self._console = None
            self._args = args
            self._kwargs = kwargs

        # --------------------------------------------------------------
        def __enter__(self):
            if not self._lazy:
                self._getconsole()
            return self

        # --------------------------------------------------------------
        def __exit__(self, type, value, traceback):
            if not self._lazy:
                self._getconsole().quit()
                self._console = None

        # --------------------------------------------------------------
        def __call__(self, aCmd=None, aMaxLen=1):
            # FIXME: only needed because of VivadoProjectMaker
            # Fix at source and remove
            console = self._getconsole()
            if aCmd is None:
                return

            if aCmd.count('\n') is not 0:
                aCmd = aCmd.split('\n')

            if isinstance(aCmd, str):
                return console.execute(aCmd, aMaxLen)
            elif isinstance(aCmd, list):
                return console.executeMany(aCmd, aMaxLen)
            else:
                raise TypeError('Unsupported command type ' + type(aCmd).__name__)

    return LazyConsoleCtxClass



# -------------------------------------------------------------------------
class TCLConsoleSnoozer(object):
    """
    Snoozes notifications from Vivado
    """
    # --------------------------------------------------------------
    def __init__(self, aConsole):
        super(TCLConsoleSnoozer, self).__init__()
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


# -------------------------------------------------------------------------
# def generate_lazy_console(aTCLConsoleClass):

#     class TCLLazyConsole(object):
#         """
#         docstring for TCLLazyConsole
#         """
#         def __init__(self, *args, **kwargs):
#             super(TCLLazyConsole, self).__init__()
#             self._args = args
#             self._kwargs = kwargs
#             self._console = None

#         def get(self):
#             if not self._console:
#                 self._console = aTCLConsoleClass(*self._args, **self._kwargs)
#             return self

            