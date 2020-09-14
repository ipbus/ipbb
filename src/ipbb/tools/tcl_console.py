
# -------------------------------------------------------------------------
def consolectxmanager(aTCLConsoleClass):
    
    class TCLConsoleSessionAdapter(object):
        """
        VivadoConsole wrapper for with statements


        with XXX(_sid='pippo', ) as console:

        """

        # --------------------------------------------------------------
        def __init__(self, *args, **kwargs):
            """Constructor
            
            Args:
                *args: console arguments
                **kwargs: List of console key'd arguments
            
            """
            super(TCLConsoleSessionAdapter, self).__init__()
            self._console = None
            self._args = args
            self._kwargs = kwargs

        # --------------------------------------------------------------
        def __enter__(self):
            self._console = aTCLConsoleClass(*self._args, **self._kwargs)
            return self._console

        # --------------------------------------------------------------
        def __exit__(self, type, value, traceback):

            if self._console:
                self._console.close()
                self._console = None

    return TCLConsoleSessionAdapter



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

