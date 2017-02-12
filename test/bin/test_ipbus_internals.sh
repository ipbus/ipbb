#!/usr/bin/env bash

# Stop on the first error
set -e

ipbb init ipbus_internals
cd ipbus_internals
TEST_ROOT=$(pwd)

# Import ipbus repository
ipbb add git git@github.com:tswilliams/ipbus-fw-beta4.git -b ipbb_integration


# Simulation
ipbb proj create sim sim ipbus-fw-beta4:boards/sim
cd work/sim
ipbb sim ipcores
ipbb sim fli 
ipbb sim project
./vsim -c work.top -do "run 10 us; quit"

exit 0

# Vivado projects
TEST_PROJ_ARRAY=(enclustra_ax3_pm3_a35 enclustra_ax3_pm3_a50 kc705_basex kc705_gmii kcu105_basex)

for TEST_PROJ in "${TEST_PROJ_ARRAY[@]}"; do
    echo "#------------------------------------------------"
    echo "# Testing ${TEST_PROJ}"
    echo "#------------------------------------------------"
    cd ${TEST_ROOT}
    ipbb proj create vivado -t top_${TEST_PROJ}.dep ${TEST_PROJ} ipbus-fw-beta4:projects/example
    cd work/${TEST_PROJ}
    set +e
    ipbb vivado project synth impl bitfile || echo "ERROR: ${TEST_PROJ} build failed" >> ${TEST_ROOT}/failures.log
    set +e
done

echo ""
cat ${TEST_ROOT}/failures.log



