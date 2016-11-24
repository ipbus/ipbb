#!/usr/bin/env bash

set -e

BUILD_AREA="xyz"

ipbb init ${BUILD_AREA}
cd ${BUILD_AREA}
ipbb add git https://:@gitlab.cern.ch:8443/ipbus/dummy-fw-proj.git
ipbb add git https://:@gitlab.cern.ch:8443/ipbus/ipbus-fw-dev.git -b kc705
ipbb add svn svn+ssh://thea@svn.cern.ch/reps/cactus/trunk/cactusupgrades -s boards/mp7 -s components -s projects/examples

exit 0

HERE=$(pwd)
cd ${BUILD_AREA}

ipbb vivado create kc705 dummy-fw-proj:projects/example top_kc705_gmii.dep
cd kc705
ipbb vivado project
ipbb vivado build
ipbb vivado bitfile

cd ${HERE}

ipbb vivado create mp7xe_690_minimal cactusupgrades:projects/examples/mp7xe_690_minimal top.dep
cd mp7xe_690_minimal
ipbb vivado project
ipbb vivado build
ipbb vivado bitfile
