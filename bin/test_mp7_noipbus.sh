#!/usr/bin/env bash


CACTUS_USER="thea"

ipbb init mp7_noipbus
cd mp7_noipbus

ipbb add git https://:@gitlab.cern.ch:8443/ipbus/ipbus-fw-beta3.git
ipbb add svn svn+ssh://${CACTUS_USER}@svn.cern.ch/reps/cactus/trunk/cactusupgrades -s boards/mp7 -s components -s projects/examples


rm -rf source/cactusupgrades/components/{ipbus_*,opencores_*}
find source/cactusupgrades/ -type f -name '*.dep' -print0 | xargs -0 sed -i 's#\(-c \)\(components/\(ipbus_\|opencores_\)\)#\1ipbus-fw-beta3:\2#'


