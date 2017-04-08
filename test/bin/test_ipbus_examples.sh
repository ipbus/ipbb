#!/usr/bin/env bash

ALL_EXAMPLES="enclustra_ax3_pm3_a35 enclustra_ax3_pm3_a50 kc705_basex kc705_gmii kcu105_basex sim"

if [[ "$#" -gt 1 ]]; then
    echo "Usage $(basename $0) <project>"
    for PROJ in ${ALL_EXAMPLES}; do
        echo "  - $PROJ"
    done
    echo    
    exit
elif [[ "$#" -eq 0 ]]; then
    EXAMPLES=${ALL_EXAMPLES}
elif [[ "$#" -eq 1 ]]; then
    if [[ ${ALL_EXAMPLES} != *" $1 "* ]]; then
        echo "Example '$1' does not exist."
        echo
        echo "Available choiches:"
        for PROJ in ${ALL_EXAMPLES}; do
            echo "  - $PROJ"
        done
        echo
        exit
    else
        EXAMPLES=$1
    fi
fi



# Stop on the first error
set -e
set -x

rm -rf ipbus-fw-examples

ipbb init ipbus-fw-examples
cd ipbus-fw-examples
TEST_ROOT=$(pwd)

# Import ipbus repository
# ipbb add git git@github.com:ipbus/ipbus-firmware.git
ipbb add tar https://github.com/ipbus/ipbus-firmware/archive/master.tar.gz -s1 -d ipbus-firmware


for EXAMPLE in ${EXAMPLES}; do
    echo ${EXAMPLE}
    time src/ipbus-firmware/tests/ci/test_build.sh ${EXAMPLE}
done
