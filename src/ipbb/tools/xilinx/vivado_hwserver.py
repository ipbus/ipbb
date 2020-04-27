from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------

from .vivado_console import VivadoConsole
from .tcl_console import lazyctxmanager, TCLConsoleSnoozer

# -------------------------------------------------------------------------
class VivadoHWServer(VivadoConsole):

    """Vivado Harware server object

    Exposes a standard interface for programming devices.
    """
    
    # --------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super(VivadoHWServer, self).__init__(*args, **kwargs)

    # --------------------------------------------------------------
    def openHw(self):
        return self.execute('open_hw')

    # --------------------------------------------------------------
    def connect(self, uri=None):
        lCmd = ['connect_hw_server']
        if uri is not None:
            lCmd += ['-url ' + uri]
        return self.execute(' '.join(lCmd))

    # --------------------------------------------------------------
    def getHwTargets(self):
        return self.execute('get_hw_targets')[0].split()

    # --------------------------------------------------------------
    def openHwTarget(self, target, is_xvc=False):
        return self.execute('open_hw_target {1} {{{0}}}'.format(target, '-xvc_url' if is_xvc else ''))

    # --------------------------------------------------------------
    def closeHwTarget(self, target=None):
        lCmd = 'close_hw_target' + ('' if target is None else ' ' + target)
        return self.execute(lCmd)

    # --------------------------------------------------------------
    def getHwDevices(self):
        return self.execute('get_hw_devices')[0].split()

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
@lazyctxmanager
class VivadoHWOpen(VivadoHWServer):
    """
    docstring for VivadoHWOpen
    """
    pass
