#!/usr/bin/env bash

# Stop on the first error
set -e
set -x

rm -rf ipbus-fw-examples

ipbb init ipbus-fw-examples
cd ipbus-fw-examples
TEST_ROOT=$(pwd)

# Import ipbus repository
ipbb add git git@github.com:ipbus/ipbus-firmware.git

EXAMPLES="enclustra_ax3_pm3_a35 enclustra_ax3_pm3_a50 kc705_basex kc705_gmii kcu105_basex sim"
for EXAMPLE in ${EXAMPLES}; do
    echo ${EXAMPLE}
    time src/ipbus-firmware/tests/ci/test_build.sh ${EXAMPLE}
done
