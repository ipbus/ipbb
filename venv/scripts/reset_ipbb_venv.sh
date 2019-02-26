#!/bin/bash
# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)
# Loading common stuff
source ${HERE}/common_ipbb_venv.sh

if [ -z "$IPBB_ROOT" ]; then
    echo -e "${COL_RED}IPBB environment not set up. Quitting.${COL_NULL}"
    exit 0
fi

rm -rf ${IPBB_VENV}
rm -rf ${IPBB_ROOT}/ipbb.egg-info

echo "Deleted ${IPBB_VENV}. Please deactivate the environment before continuing."