#!/usr/bin/env bash


if [[ "$#" -ne 1 ]]; then
    echo "Usage: $(basename $0) <cactus user>"
    exit
else
    CACTUS_USER="$1"
fi

CACTUS_USER="${CACTUS_USER:-${USER}}"

echo "Using CACTUS_USER: ${CACTUS_USER}"

# Stop on error
set -e 

ipbb init mp7_noipbus
cd mp7_noipbus

ipbb add git https://:@gitlab.cern.ch:8443/ipbus/ipbus-fw-beta3.git
ipbb add svn svn+ssh://${CACTUS_USER}@svn.cern.ch/reps/cactus/trunk/cactusupgrades -s boards/mp7 -s components -s projects/examples

# Eliminate ipbus & relink to external repository
rm -rf "source/cactusupgrades/components/{ipbus_*,opencores_*}"
find "source/cactusupgrades/" -type f -name '*.dep' -print0 | xargs -0 sed -i 's#\(-c \)\(components/\(ipbus_\|opencores_\)\)#\1ipbus-fw-beta3:\2#'

ipbb proj create vivado mp7xe_690_minimal cactusupgrades:projects/examples/mp7xe_690_minimal

# replace v7_690es.dep with v7_690es_new.dep in
# ../../source/cactusupgrades/boards/mp7/base_fw/mp7_690es/firmware/cfg/mp7_690es.dep
# ../../source/cactusupgrades/boards/mp7/base_fw/mp7xe_690/firmware/cfg/mp7xe_690.dep
sed -i 's#v7_690es.dep#v7_690es_new.dep#' source/cactusupgrades/boards/mp7/base_fw/{mp7_690es/firmware/cfg/mp7_690es.dep,mp7xe_690/firmware/cfg/mp7xe_690.dep}

# Delete synchroniser.vhd from cactusupgrades/components/mp7_infra/firmware/cfg/mp7xe_infra.dep
sed -i 's# synchroniser.vhd##' source/cactusupgrades/components/mp7_infra/firmware/cfg/mp7xe_infra.dep

cd work/mp7xe_690_minimal

ipbb vivado project
ipbb vivado synth