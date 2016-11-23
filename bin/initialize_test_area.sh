#!/usr/bin/env bash

set -e

BUILD_AREA="xyz"

ipbb init ${BUILD_AREA}
cd ${BUILD_AREA}
ipbb add git https://:@gitlab.cern.ch:8443/ipbus/dummy-fw-proj.git
ipbb add git https://:@gitlab.cern.ch:8443/ipbus/ipbus-fw-dev.git -b kc705
ipbb add svn svn+ssh://thea@svn.cern.ch/reps/cactus/trunk/cactusupgrades -s boards/mp7 -s components -s projects/examples