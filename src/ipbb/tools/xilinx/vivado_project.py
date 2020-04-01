from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------

from .vivado_console import VivadoConsole

# ------------------------------------------------------------------------------
class VivadoProject(object):
    """docstring for VivadoProject"""
    def __init__(self, console):
        super(VivadoProject, self).__init__()
        self.console = console

    def current(self):
        """Name of the current prokecy, if any"""
        return self.console('current_project -quiet')[0]
    
    def open(self, aPath):

        if self.current():
            self.close()

        self.console('open_project {}'.format(aPath))

    def create(self):
        pass

    def close(self):
        self.console('close_project')

    def listfiles(self):
        
        lConsole = self.console
        lFiles = {}
        lFileSets = lConsole('get_filesets')[0].split()
        for s in lFileSets:
            x = lConsole('get_files -quiet -of [get_fileset {}]'.format(s))[0]
            lFiles[s] = x.split() if x else None
        # lSources = lConsole('get_files -of [get_fileset sources_1]')[0].split()
        # lConstrs = lConsole('get_files -of [get_fileset constrs_1]')[0].split()
        # lUtils = lConsole('get_files -of [get_fileset utils_1]')[0].split()
        lIPs = lConsole('get_ips -quiet')[0]
        # print(lIPs)
        lXcis = []
        for ip in lIPs.split():
            lXcis += lConsole('get_property IMPORTED_FROM [get_files -of [get_filesets {0}] {0}.xci]'.format(ip))
        
        lFiles['ips'] = lXcis
        return lFiles