#!/usr/bin/env bash

AREA_NAME="myarea"

set -e
set -x

ipbb init ${AREA_NAME}
cd ${AREA_NAME}
FW_ROOT=$(pwd)

ipbb add git https://:@gitlab.cern.ch:8443/ipbus/dummy-fw-proj.git
ipbb add git https://:@gitlab.cern.ch:8443/ipbus/ipbus-fw-dev.git -b kc705
ipbb add svn svn+ssh://thea@svn.cern.ch/reps/cactus/trunk/cactusupgrades -s boards/mp7 -s components -s projects/examples


cd ${FW_ROOT}
ipbb proj create vivado kc705 dummy-fw-proj:projects/example -t top_kc705_gmii.dep
cd work/kc705
ipbb vivado project 
ipbb vivado build
ipbb vivado bitfile


cd ${FW_ROOT}
ipbb proj create vivado mp7xe_690_minimal cactusupgrades:projects/examples/mp7xe_690_minimal 
cd work/mp7xe_690_minimal
ipbb vivado project
ipbb vivado build
ipbb vivado bitfile


cd ${FW_ROOT}
ipbb proj create sim mp7_sim cactusupgrades:projects/examples/mp7_sim 
cd work/mp7_sim
ipbb sim ipcores
ipbb sim fli 
ipbb sim project
./vsim -c work.top -do "run 10 us; quit"
set +x