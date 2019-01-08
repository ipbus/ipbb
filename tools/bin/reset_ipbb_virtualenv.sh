#!/bin/bash


if [ -z "$IPBB_ROOT" ]; then
    echo "IPBB environment not set up. Exiting."
    exit 0
fi

rm -r ${IPBB_ROOT}/external
rm -r ${IPBB_ROOT}/ipbb.egg-info

echo "Deleted ${IPBB_ROOT}/external. Please deactivate the environment before continuing."