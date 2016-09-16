from . import WorkareaBuilder

import logging
import os

#------------------------------------------------------------------------------
#  _   ___              __     ___                ___       _ __   __
# | | / (_)  _____ ____/ /__  / _ | _______ ___ _/ _ )__ __(_) /__/ /__ ____
# | |/ / / |/ / _ `/ _  / _ \/ __ |/ __/ -_) _ `/ _  / // / / / _  / -_) __/
# |___/_/|___/\_,_/\_,_/\___/_/ |_/_/  \__/\_,_/____/\_,_/_/_/\_,_/\__/_/
#
#------------------------------------------------------------------------------
mkVivadoTemplate='''
BUILD_PROJECT:={REPLACE_BUILD_PROJECT}
TOPLVL:={REPLACE_TOPLVL}
PROJNAME:=top
CACTUS_ROOT:={CACTUS_ROOT}
SCRIPT_PATH:={SCRIPT_PATH}

# Derived paths
UPGRADES_ROOT:=$(CACTUS_ROOT)
DEPTREE:=$(SCRIPT_PATH)/dep_tree.py

# Timestamp
TIMESTAMP=$(shell date +%y%m%d_%H%M)

# Define target filenames
ifdef name
PKGNAME=$(name)
else
PKGNAME:=$(TOPLVL)
endif

DEPFILE:=$(TOPLVL).dep
PROJECTFILE:=$(PROJNAME)/$(PROJNAME).xpr
BITFILE:=$(PROJNAME)/$(PROJNAME).runs/impl_1/$(PROJNAME).bit
PACKAGEFILE:=$(PKGNAME)_$(TIMESTAMP).tgz


# Tcl commands
define TCL_BUILD_BITFILE
open_project $(PROJECTFILE)
launch_runs synth_1
wait_on_run synth_1
launch_runs impl_1
wait_on_run impl_1
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1
exit
endef
export TCL_BUILD_BITFILE

define TCL_RESET_PROJECT
open_project $(PROJECTFILE)
reset_run synth_1
exit
endef
export TCL_RESET_PROJECT

.PHONY: clean reset addrtab decode

$(PROJECTFILE):
\t@$(DEPTREE) -p v $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o mkProject.tcl
\t@vivado -mode batch -source mkProject.tcl

$(BITFILE):
\t@echo "$$TCL_BUILD_BITFILE" > mkBitfile.tcl
\tvivado -mode batch -source mkBitfile.tcl

$(PACKAGEFILE): addrtab bitfile
\tmkdir -p pkg/src
\tcp $(BITFILE) pkg/src/
\tcp -a addrtab/ pkg/src/
\ttar cvfz pkg/$(PACKAGEFILE) -C pkg/src addrtab $(PROJNAME).bit

project: $(PROJECTFILE)

bitfile: $(BITFILE)

package: $(PACKAGEFILE)

clean:
\t@dir -1 | grep -v Makefile | xargs rm -rf

reset:
\trm -f $(BITFILE)
\t@echo "$$TCL_RESET_PROJECT" > resetProject.tcl
\tvivado -mode batch -source resetProject.tcl


addrtab:
\t@echo "Collecting address tables..."
\t@mkdir -p addrtab
\t@$(DEPTREE) -p a $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) | xargs -tI: cp : addrtab
\t@echo "Done."

decode: addrtab
\trm -rf decoders
\tcp -a addrtab decoders
\t$(DEPTREE) -p b $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o decoders/update.sh
\tchmod a+x decoders/update.sh
\texport PATH=/opt/cactus/bin/uhal/tools:$$PATH; cd decoders && ./update.sh
'''

#------------------------------------------------------------------------------
# VivadoAreaBuilder implementation
#------------------------------------------------------------------------------
class VivadoAreaBuilder(WorkareaBuilder):
    _log = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(VivadoAreaBuilder,self).__init__(**kwargs)

    def make(self,workarea,env):
        from os.path import join

        self._log.info('Creating a new Vivado area')
        try:
            os.makedirs(workarea)
        except:
            self._log.info('Directory %s exists' % workarea)

        # Vivado: create makefile
        mkviv=join(workarea,'Makefile')

        with open(mkviv,'w') as f:
            f.write(
                mkVivadoTemplate.format(**env)
                )
            self._log.info('File %s created' % mkviv)
