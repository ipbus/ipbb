from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems
# ------------------------------------------------------------------------------

# Modules
import time 

# Specific module elements
from future.utils import iterkeys, itervalues, iteritems

from ..defaults import kTopEntity
from os.path import abspath, join, split, splitext, dirname

class VivadoHlsProjectMaker(object):
    """
    docstring for VivadoHlsProjectMaker
    """
    # --------------------------------------------------------------
    def __init__(self, aProjInfo):
        self.projInfo = aProjInfo

    # --------------------------------------------------------------
    def write(self, aOutput, aSettings, aComponentPaths, aCommandList, aLibs):

        write = aOutput

        lReqVariables = {'device_name', 'device_package', 'device_speed'}
        if not lReqVariables.issubset(aSettings.keys()):
            raise RuntimeError("Missing required variables: {}".format(lReqVariables.difference(aSettings)))
        lXilinxPart = "{device_name}{device_package}{device_speed}".format(**aSettings)

        # ----------------------------------------------------------
        write = aOutput
        
        lWorkingDir = abspath(join(self.projInfo.path, self.projInfo.name))
        lTopEntity = aSettings.get('top_entity', kTopEntity)


        # ----------------------------------------------------------

        write('# Autogenerated project build script')
        write(time.strftime("# %c"))
        write()

        write(
            'open_project -reset {0} '.format(self.projInfo.name)
        )

        for setup in (c for c in aCommandList['setup'] if not c.finalize):
            write('source {0}'.format(setup.filepath))

        lHlsSrcs = aCommandList['hlssrc'] 

        lIncludePaths = set()
        for src in lHlsSrcs:
            lIncludePaths.add(dirname(src.filepath))
        # print(lIncludePaths)

        lCFlags = lCSimFlags = ' '.join( ( '-I'+ipath for ipath in lIncludePaths) )

        for src in lHlsSrcs:


            # lLocalIncludes = 

            opts = []
            if src.testbench:
                opts += ['-tb']
            if lCFlags or src.cflags:
                opts += ['-cflags {{{}}}'.format(' '.join( (f for f in (lCFlags, src.cflags) if f)))]
            if lCSimFlags or src.csimflags:
                opts += ['-csimflags {{{}}}'.format(' '.join( (f for f in (lCSimFlags, src.csimflags) if f)))]

            lCommand = 'add_files {} {}'.format(' '.join(opts), src.filepath)
            write(lCommand)


        write('open_solution -reset sol1')
        write('set_part {{{0}}} -tool vivado'.format(lXilinxPart))

        write('set_top {}'.format(lTopEntity))

        for setup in (c for c in aCommandList['setup'] if c.finalize):
            write('source {0}'.format(setup.filepath))

        write('close_project')
    # --------------------------------------------------------------