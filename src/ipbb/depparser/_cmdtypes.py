from __future__ import print_function, absolute_import
from future.utils import iteritems

# -----------------------------------------------------------------------------
class Command(object):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd       (str): command directive
        filepath  (str): absolute, normalised path to the command target.
        package   (str): package the target belongs to.
        component (str): component withon 'Package' the target belongs to
    """

    # --------------------------------------------------------------
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aCd):
        super(Command, self).__init__()
        self.cmd = aCmd
        self.filepath = aFilePath
        self.package = aPackage
        self.component = aComponent
        self.cd = aCd

    # --------------------------------------------------------------
    def __str__(self):

        lFlags = self.flags()
        lExtra = self.extra()
        lFields = [
            '\'{}\''.format(self.filepath),
            'flags: '+(str(lFlags) if lFlags else 'none'),
            'component: \'{}:{}\''.format(self.package, self.component),
            ('extra: { '+str(lExtra)+' }') if lExtra else None
            ]
        return '{{ {0} }}'.format(', '.join(f for f in lFields if f is not None))

    # --------------------------------------------------------------
    def __eq__(self, other):
        return (self.filepath == other.filepath)

    # --------------------------------------------------------------
    def flags(self):
        return []

    # --------------------------------------------------------------
    def extra(self):
        return None

    __repr__ = __str__


# -----------------------------------------------------------------------------
class SrcCommand(Command):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd        (str):  command directive
        filepath   (str):  absolute, normalised path to the command target.
        package    (str):  package the target belongs to.
        component  (str):  component withon 'Package' the target belongs to
        lib        (str):  library the file will be added to
        vhdl2008   (bool): toggles the vhdl 2008 syntax for .vhd files
        useinsynth (bool): use this files in synth
        useinsim   (bool): use this files in sim
    """
    # --------------------------------------------------------------
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aCd, aLib, aVhdl2008, aUseInSynth, aUseInSim):
        super(SrcCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent, aCd)

        self.lib = aLib
        self.vhdl2008 = aVhdl2008
        self.useInSynth = aUseInSynth
        self.useInSim = aUseInSim

    # --------------------------------------------------------------
    def flags(self):
        lFlags = []
        if self.vhdl2008:
            lFlags.append('vhdl2008')
        if self.useInSynth:
            lFlags.append('synth')
        if self.useInSim:
            lFlags.append('sim')

        return lFlags

    # --------------------------------------------------------------
    def __eq__(self, other):
        return (self.filepath == other.filepath) and (self.lib == other.lib)


# -----------------------------------------------------------------------------
class HlsSrcCommand(Command):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd        (str):  command directive
        filepath   (str):  absolute, normalised path to the command target.
        package    (str):  package the target belongs to.
        component  (str):  component withon 'Package' the target belongs to
        cflags     (str):  c compiler flags
        csimflags  (str):  c compiler flags in simulation
        testbench  (bool): this file is a testbench
    """
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aCd, aCFlags, aCSimFlags, aTestBench, aIncludeComps):
        super(HlsSrcCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent, aCd)
        self.cflags = aCFlags
        self.csimflags = aCSimFlags
        self.testbench = aTestBench
        self.includeComponents = aIncludeComps

    # --------------------------------------------------------------
    def flags(self):
        lFlags = []
        if self.testbench:
            lFlags.append('tb')

        return lFlags
        
    def extra(self):
        if not self.includeComponents:
            return None
        return 'includes: '+str(['{}:{}'.format(p, c) for p,c in self.includeComponents])

# -----------------------------------------------------------------------------
class SetupCommand(Command):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd       (str):  command directive
        filepath  (str):  absolute, normalised path to the command target.
        package   (str):  package the target belongs to.
        component (str):  component withon 'Package' the target belongs to
        finalise  (bool): setup-only flag, identifies setup scripts to be executed at the end
    """
    # --------------------------------------------------------------
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aCd, aFinalise):
        super(SetupCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent, aCd)

        self.finalize = aFinalise

    # --------------------------------------------------------------
    def flags(self):
        return ['finalise'] if self.finalize else []


# -----------------------------------------------------------------------------
class AddrtabCommand(Command):
    """Container class for dep commands parsed form dep files

    Attributes:
        cmd       (str):  command directive
        filepath  (str):  absolute, normalised path to the command target.
        package   (str):  package the target belongs to.
        component (str):  component withon 'Package' the target belongs to
        toplevel  (bool): addrtab-only flag, identifies address table as top-level
    """
    # --------------------------------------------------------------
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aCd, aTopLevel):
        super(AddrtabCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent, aCd)
        self.toplevel = aTopLevel

    # --------------------------------------------------------------
    def flags(self):
        return ['toplevel'] if self.toplevel else []


# -----------------------------------------------------------------------------
class IncludeCommand(Command):
    """    Attributes:
        cmd       (str):  command directive
        filepath  (str):  absolute, normalised path to the command target.
        package   (str):  package the target belongs to.
        component (str):  component withon 'Package' the target belongs to
    """
    def __init__(self, aCmd, aFilePath, aPackage, aComponent, aCd, aDepFileObj=None):
        super(IncludeCommand, self).__init__(aCmd, aFilePath, aPackage, aComponent, aCd)
        self.depfile = aDepFileObj
