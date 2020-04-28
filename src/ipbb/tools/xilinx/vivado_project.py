from __future__ import print_function, absolute_import
from builtins import range
import six
# ------------------------------------------------------------------------------

from os.path import join, dirname, splitext, abspath
from .vivado_console import VivadoConsole

# ------------------------------------------------------------------------------
class VivadoProject(object):
    """docstring for VivadoProject"""
    def __init__(self, aConsole, aPath=None):
        super(VivadoProject, self).__init__()
        self.console = aConsole

        if aPath:
            self.open(aPath)

    def current(self):
        """
        Name of the current prokect, if any
        
        :returns:   Name of the currently opened projecty
        :rtype:     string
        """
        return self.console('current_project -quiet')[0]

    def get_property(self, name):
        """
        Gets the property.
        
        :param      name:  The property name
        :type       name:  string
        
        :returns:   The property value.
        :rtype:     string
        """
        return  self.console('get_property {}} [current_project]'.format(name))[0]
    
    def open(self, aPath):
        """
        Open a project
        
        :param      aPath:  Path of the project file (.xpr)
        :type       aPath:  string
        
        :returns:   { description_of_the_return_value }
        :rtype:     { return_type_description }
        """

        cp = self.current()
        if cp:
            # cp_dir = self.console('get_property DIRECTORY [current_project]')[0]
            cp_dir = self.get_property('DIRECTORY')

            # Use the path to check if the open project and the requested are the same
            if abspath(join(cp_dir, cp+'.xpr')) == abspath(aPath):
                # They are, do nothing
                return

            # Close it otherwise
            self.close()

        # Open the right one
        self.console('open_project {}'.format(aPath))

    def create(self):
        pass

    def close(self):
        """
        Close current project
        """
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