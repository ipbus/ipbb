#!/bin/bash
# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)
# Loading common stuff
source ${HERE}/common_ipbb_venv.sh


if [ -d "${IPBB_VENV}" ] ; then
    echo -e "${COL_YELLOW}WARNING: ${IPBB_VENV} already exists. Delete it before running $(basename $SH_SOURCE).${COL_NULL}"
else
    echo -e "${COL_YELLOW}Virtualenv ${IPBB_VENV} does not exist.${COL_NULL}"
    echo -e "${COL_GREEN}Setting up a new virtual python environment in ${IPBB_VENV}${COL_NULL}"

    IPBB_PIP_INSTALLOPT="-U -I -q"
    IPBB_PIP_INSTALLOPT="-U -I"

    virtualenv-3.6 ${IPBB_VENV} --no-site-packages
    source ${IPBB_VENV}/bin/activate

    echo -e "${COL_BLUE}Upgrading python tools...${COL_NULL}"

    # upgrade pip to the latest greatest version
    pip install ${IPBB_PIP_INSTALLOPT} pip setuptools

    echo -e "${COL_BLUE}Installing ipbb...${COL_NULL}"

    pip install ${IPBB_PIP_INSTALLOPT} --no-cache-dir --editable ${IPBB_ROOT}

    echo -e "${COL_GREEN}Setup completed${COL_NULL}"
    deactivate
fi