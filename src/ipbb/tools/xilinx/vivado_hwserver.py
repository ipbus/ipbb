from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------

from .vivado_console import VivadoConsole

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
class VivadoOpen(object):
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
        super(VivadoOpen, self).__init__()
        self._args = args
        self._kwargs = kwargs

    # --------------------------------------------------------------
    def __enter__(self):
        self._console = VivadoConsole(*self._args, **self._kwargs)
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
