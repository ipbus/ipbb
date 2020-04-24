from __future__ import print_function, absolute_import
from future.utils import iterkeys, itervalues, iteritems
# ------------------------------------------------------------------------------

from ..defaults import kTopEntity
from os.path import abspath, join, split, splitext

class VivadoHlsProjectMaker(object):
    """
    docstring for VivadoHlsProjectMaker
    """
    # --------------------------------------------------------------
    def __init__(self, aProjInfo):
        self.projInfo = aProjInfo

    # --------------------------------------------------------------
    def write(self, aTarget, aSettings, aComponentPaths, aCommandList, aLibs):

        write = aTarget

        lReqVariables = {'device_name', 'device_package', 'device_speed'}
        if not lReqVariables.issubset(aSettings.keys()):
            raise RuntimeError("Missing required variables: {}".format(lReqVariables.difference(aSettings)))
        lXilinxPart = "{device_name}{device_package}{device_speed}".format(**aSettings)

        lWorkingDir = abspath(join(self.projInfo.path, self.projInfo.name))
        lTopEntity = aSettings.get('top_entity', kTopEntity)


        write(
            'open_project {0} -reset'.format(self.projInfo.name)
        )


        lHlsSrcs = aCommandList['hlssrc'] 

        print(lHlsSrcs)

        for src in lHlsSrcs:

            opts = []
            if src.testbench:
                opts += ['-tb']
            if src.cflags:
                opts += ['-cflags {}'.format(src.cflags)]
            if src.csimflags:
                opts += ['-csimflags {}'.format(src.csimflags)]

            lCommand = 'add_file {} {}'.format(' '.join(opts), src.filepath)
            write(lCommand)


        write('open_solution solution1')
        write('set_part {{{0}}} -tool vivado'.format(lXilinxPart))
