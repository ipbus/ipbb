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



