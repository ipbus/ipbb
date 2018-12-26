from __future__ import print_function
# ------------------------------------------------------------------------------

import time
import os
import shutil


# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
class SimlibMaker(object):
    """Simulation library generator script
    
    Attributes:
        simlibPath (string): Destination path of the library
        simulator (string): Simulator name (as defined by vivado)
        unisimNoDebug (int): Enable Unisim library debug
    """


    def __init__(self, aSimulator, aSimlibPath, aUnisimNoDebug=0):

        super(SimlibMaker, self).__init__()
        self.simlibPath = aSimlibPath
        self.simulator = aSimulator
        self.unisimNoDebug = aUnisimNoDebug

    def write(self, aTarget):
        write = aTarget

        if self.unisimNoDebug == 1:  # If the encrypted library uses unisim
            # Yeah... Incorrectly documented by Vivado They change the variable
            # name used for questa on this option only.
            lCfgSimRoot = self.simulator if self.simulator != 'questa' else 'questasim'
            write('config_compile_simlib -cfgopt {{ {}.vhdl.unisim: -nodebug}}'.format(lCfgSimRoot))

        write(
            'compile_simlib -verbose -simulator {} -family all -language all -library all -dir {{{}}}'.format(self.simulator, self.simlibPath)
        )
# --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
