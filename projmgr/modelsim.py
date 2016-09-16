from . import WorkareaBuilder

import logging
import os

#------------------------------------------------------------------------------
#    __  ___        __    __    _       ___                ___       _ __   __
#   /  |/  /__  ___/ /__ / /__ (_)_ _  / _ | _______ ___ _/ _ )__ __(_) /__/ /__ ____
#  / /|_/ / _ \/ _  / -_) (_-</ /  ' \/ __ |/ __/ -_) _ `/ _  / // / / / _  / -_) __/
# /_/  /_/\___/\_,_/\__/_/___/_/_/_/_/_/ |_/_/  \__/\_,_/____/\_,_/_/_/\_,_/\__/_/
#                                                                                   #
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Environment template
#------------------------------------------------------------------------------

envSimTemplate='''
#!/bin/bash

# Comment this line after customizing the environment
# warning && return 1

# Check for Xilinx environment
if [ -z "$XILINX_VIVADO" ]; then
echo "No Xilinx, no party"
return
fi

# Path to modelsim executables
# export PATH=$PATH:/software/CAD/Mentor/2013_2014/Questa/HDS_2012.2b/questasim/bin

# This makes it go fast
MTI_VCO_MODE=64

# Where to find the various libraries and headers
MODELSIM_ROOT=${MODELSIM_ROOT:-"/opt/mentor/modeltech/"}

# Add it to the path to make finding modelsim easier
PATH="${MODELSIM_ROOT}/bin:${PATH}"

# Location of pre-compiled Xilinx libraries
XILINX_SIMLIBS=.xil_sim_libs/$(basename ${XILINX_VIVADO})

vars="MODELSIM_ROOT"

notfound=0
for v in $vars; do
    echo ${v} ${!v}
    if [ ! -d "${!v}" ]; then
        echo "WARNING: $v does not exits"
        (( notfound++ ))
    fi
done

if [ $notfound -ne 0 ]; then
   echo "Some directoried were not found. Check the settings in this file";
   echo "No environment variable was set";
   return;
fi

export PATH MTI_VCO_MODE MODELSIM_ROOT XILINX_SIMLIBS
'''


#------------------------------------------------------------------------------
# Makefile template
#------------------------------------------------------------------------------

mkSimTemplate='''
BUILD_PROJECT:={REPLACE_BUILD_PROJECT}
TOPLVL:={REPLACE_TOPLVL}
CACTUS_ROOT:={CACTUS_ROOT}
SCRIPT_PATH:={SCRIPT_PATH}

DEPFILE:=$(TOPLVL).dep

# Derived paths
UPGRADES_ROOT:=$(CACTUS_ROOT)
DEPTREE:=$(SCRIPT_PATH)/dep_tree.py
IPSIM_FOLDER:=$(TOPLVL)/$(TOPLVL).srcs/sources_1/ip

.PHONY: help project fli _checkenv ipsim addrtab decode

help:
\t@echo "Please choose one of the following target: project bitfile addrtab package clean cleanproject"

project: _checkenv fli ipsim

\t$(DEPTREE) -p s $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o mkProject.tcl
\t$(MODELSIM_ROOT)/bin/vsim -c -do "do mkProject.tcl; quit"

ipsim: .ipcores_sim_built
# ipsim: $(IPSIM_FOLDER)/built

# $(IPSIM_FOLDER)/built:
.ipcores_sim_built:
\techo Building IPCores simulation
\t$(DEPTREE) -p ip $(UPGRADES_ROOT) $(BUILD_PROJECT) $(DEPFILE) -o mkSimIPs.tcl
\tvivado -mode batch -source mkSimIPs.tcl

fli: _checkenv mac_fli.so

mac_fli.so:
\trm -rf modelsim_fli
\tcp -a $(UPGRADES_ROOT)/components/ipbus_eth/firmware/sim/modelsim_fli ./
\tcd modelsim_fli && ./mac_fli_compile.sh
\tcp modelsim_fli/mac_fli.so .

_checkenv:
ifndef MODELSIM_ROOT
\t$(error MODELSIM_ROOT is not defined)
endif

clean:
\t@dir -1 | grep -v -e  '^\(Makefile\|env.sh\|env_example.sh\)' | xargs rm -rf
\t@rm -rf $(XILINX_SIMLIBS)

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

class ModelsimAreaBuilder(WorkareaBuilder):
    _log = logging.getLogger(__name__)

    def __init__(self, **kwargs):
        super(ModelsimAreaBuilder,self).__init__(**kwargs)

    def make(self,workarea,env):
        from os.path import join
        self._log.info('Creating a new ModelSim area')

        try:
            os.makedirs(workarea)
        except:
            self._log.info('Directory %s exists' % workarea)

        # Modelsim: create environment file
        envsim=join(workarea,'env.sh')
        with open(envsim,'w') as f:
            f.write(
                envSimTemplate
                )
            self._log.info('File %s created' % envsim)

        # Modelsim: create makefile
        mksim = join(workarea,'Makefile')
        with open(mksim,'w') as f:
            f.write(
                mkSimTemplate.format(**env)
                )
            self._log.info('File %s created' % mksim)
