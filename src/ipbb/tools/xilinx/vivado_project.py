
from os.path import join, dirname, splitext, abspath
from collections import OrderedDict
from .vivado_console import VivadoConsole

# ------------------------------------------------------------------------------
class VivadoProject(object):
    """
    Vivado console helper class to expose project specific methonds
    
    Attributes:
        console (VivadoConsole): Console object
    """

    # ------------------------------------------------------------------------------
    def __init__(self, aConsole, aPath=None):
        """
        Constructor
        
        Args:
            aConsole (VivadoConsole): Console object
            aPath (string, optional): Project file (.xpr) path
        """
        super().__init__()
        self.console = aConsole

        if aPath:
            self.open(aPath)

    # ------------------------------------------------------------------------------
    def current(self):
        """
        Name of the current project, if any
        

        Returns:
            string: Name of current project
        
        """
        return self.console('current_project -quiet')[0]

    # ------------------------------------------------------------------------------
    def get_property(self, name):
        """
        Gets the value of a project property.
        
        Args:
            name (str): Name of the property
        
        Returns:
            str: Property value
        
        """
        return  self.console('get_property {{{}}} [current_project]'.format(name))[0]
    
    # ------------------------------------------------------------------------------
    def open(self, aPath):
        """
        Open a project
        
        Args:
            aPath (str): Project file path
        
        Returns:
            None
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

    # ------------------------------------------------------------------------------
    # def create(self):
    #     pass

    # ------------------------------------------------------------------------------
    def close(self):
        """
        Close current project
        """
        self.console('close_project')

    # ------------------------------------------------------------------------------
    def open_run(self, run_name):
        self.console('open_run {}'.format(run_name))

    # ------------------------------------------------------------------------------
    def reset_runs(self, *args):
        for r in args:
            self.console('reset_run {}'.format(r))

    # ------------------------------------------------------------------------------
    def readRunInfo(self, aProps=None):
        """Reads 
        
        Args:
            aProps (None, optional): Description
        
        Returns:
            TYPE: Description
        """
        lInfos = {}
        lProps = aProps if aProps is not None else (
            'STATUS',
            'NEEDS_REFRESH',
            'PROGRESS',
            # 'IS_IMPLEMENTATION',
            # 'IS_SYNTHESIS',
            'STATS.ELAPSED',
            # 'STATS.ELAPSED',
        )

        # Gather data about existing runs
        lRuns = self.console('get_runs')[0].split()

        for lRun in sorted(lRuns):

            lValues = (
                    self.console(f'get_property {p} [get_runs {lRun}]')[0]
                    for p in lProps
                )
            lInfos[lRun] = OrderedDict(zip(lProps, lValues))

        return lInfos

    # ------------------------------------------------------------------------------
    def listfiles(self):
        
        lConsole = self.console
        lFiles = {}
        lFileSets = lConsole('get_filesets')[0].split()
        for s in lFileSets:
            x = lConsole('get_files -quiet -of [get_fileset {}]'.format(s))[0]
            lFiles[s] = x.split() if x else None
        lIPs = lConsole('get_ips -quiet')[0]
        lXcis = []
        for ip in lIPs.split():
            lXcis += lConsole('get_property IMPORTED_FROM [get_files -quiet -of [get_filesets {0}] {{{1}}}]'.format(ip, ' '.join([ip+ext for ext in ['.xci', '.xcix']]) ))
        
        lFiles['ips'] = lXcis
        return lFiles