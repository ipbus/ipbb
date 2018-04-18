#!/bin/bash


if [ -z "$IPBB_ROOT" ]; then
    echo "IPBB environment not set up. Exiting."
    exit 0
fi

rm -r ${IPBB_ROOT}/external

echo "${IPBB_ROOT}/external. Please deactivate the environment before continuing."