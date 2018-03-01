#!/usr/bin/env bash

# Stop on error
set -e 

ipbb init mp7_noipbus
cd mp7_noipbus
ipbb add git git@github.com:ipbus/ipbus-firmware.git
ipbb add git ssh://git@gitlab.cern.ch:7999/thea/mp7.git -b standalone

ipbb proj create vivado mp7xe_690_minimal mp7:projects/examples/mp7xe_690_minimal

cd proj/mp7xe_690_minimal

ipbb vivado project
ipbb vivado synth impl bitfile


# if [[ "$#" -ne 1 ]]; then
#     echo "Usage: $(basename $0) <cactus user>"
#     exit
# else
#     CACTUS_USER="$1"
# fi

# CACTUS_USER="${CACTUS_USER:-${USER}}"

# echo "Using CACTUS_USER: ${CACTUS_USER}"




# ipbb add svn svn+ssh://${CACTUS_USER}@svn.cern.ch/reps/cactus/trunk/cactusupgrades -s boards/mp7 -s components -s projects/examples -d mp7

# MP7_REPO_NAME="mp7"

# # Eliminate ipbus & relink to external repository
# rm -rf src/${MP7_REPO_NAME}/components/{ipbus_*,opencores_*}
# find "src/${MP7_REPO_NAME}/" -type f -name '*.dep' -print0 | xargs -0 sed -i 's#\(-c \)\(components/\(ipbus_\|opencores_\)\)#\1ipbus-firmware:\2#'


# # replace v7_690es.dep with v7_690es_new.dep in
# # ../../src/${MP7_REPO_NAME}/boards/mp7/base_fw/mp7_690es/firmware/cfg/mp7_690es.dep
# # ../../src/${MP7_REPO_NAME}/boards/mp7/base_fw/mp7xe_690/firmware/cfg/mp7xe_690.dep
# sed -i 's#v7_690es.dep#v7_690es_new.dep#' src/${MP7_REPO_NAME}/boards/mp7/base_fw/{mp7_690es/firmware/cfg/mp7_690es.dep,mp7xe_690/firmware/cfg/mp7xe_690.dep}

# # Delete synchroniser.vhd from ${MP7_REPO_NAME}/components/mp7_infra/firmware/cfg/mp7xe_infra.dep
# sed -i 's# synchroniser.vhd##' src/${MP7_REPO_NAME}/components/mp7_infra/firmware/cfg/mp7xe_infra.dep
