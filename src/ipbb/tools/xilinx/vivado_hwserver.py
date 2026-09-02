
from .vivado_console import VivadoConsole
from ..tcl_console import consolectxmanager, TCLConsoleSnoozer

# -------------------------------------------------------------------------
class VivadoHWServer(VivadoConsole):

    """Vivado Harware server object

    Exposes a standard interface for programming devices.
    """
    
    # --------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # --------------------------------------------------------------
    def openHw(self):
        return self.execute('open_hw_manager')

    # --------------------------------------------------------------
    def connect(self, uri=None):
        lCmd = ['connect_hw_server']
        if uri is not None:
            lCmd += ['-url ' + uri]
        return self.execute(' '.join(lCmd))

    # --------------------------------------------------------------
    def getHwTargets(self, quiet=True):
        ret = self.execute('get_hw_targets' + (' -quiet' if quiet else ''))[0]
        return ret.split() if ret is not None else ''

    # --------------------------------------------------------------
    def openHwTarget(self, target, is_xvc=False):
        return self.execute('open_hw_target {1} {{{0}}}'.format(target, '-xvc_url' if is_xvc else ''))

    # --------------------------------------------------------------
    def closeHwTarget(self, target=None):
        lCmd = 'close_hw_target' + ('' if target is None else ' ' + '{' + target + '}' )
        return self.execute(lCmd)

    # --------------------------------------------------------------
    def getHwDevices(self, quiet=True):
        ret = self.execute('get_hw_devices' + (' -quiet' if quiet else ''))[0]
        return ret.split() if ret is not None else ''

    # --------------------------------------------------------------
    def programDevice(self, device, bitfile, probe=None):
        from os.path import abspath, normpath

        bitpath = abspath(normpath(bitfile))

        self._log.debug('Programming %s with %s', device, bitfile)

        self.execute('current_hw_device {0}'.format(device))
        self.execute(
            'refresh_hw_device -update_hw_probes {} [current_hw_device]'.format("True" if probe else 'False')
        )
        self.execute(
            'set_property PROBES.FILE {{{0}}} [current_hw_device]'.format(probe if probe else '')
        )
        self.execute(
            'set_property PROGRAM.FILE {{{0}}} [current_hw_device]'.format(bitpath)
        )
        self.execute('program_hw_devices [current_hw_device]')


# -------------------------------------------------------------------------
@consolectxmanager
class VivadoHWSession(VivadoHWServer):
    """
    docstring for VivadoHWSession
    """
    pass
