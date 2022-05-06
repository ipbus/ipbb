#!/bin/bash

declare -a missing_pypkg

function chkpypkg() {
  if ${PYTHON_CMD} -c "import pkgutil; raise SystemExit(1 if pkgutil.find_loader('${1}') is None else 0)" &> /dev/null; then
    echo "${1} is installed"
else
    echo "Error: package '${1}' is not installed"
    missing_pypkg+=(${1})
fi
}
# -----------------------------------------------------------------------------

if [ "$#" -eq 1 ]; then
    IPBB_EXTRAS_DEPS=$1
elif [ "$#" -gt 1 ]; then
    echo "Illegal number of parameters"
    return 255
fi



# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)

# Load common stuff
source ${HERE}/common_ipbb_venv.sh

if [ -z $PYTHON_PATH ]; then
    echo "ERROR: Failed to detect python3. Please install python3 and try again"
    return 1
fi

# Basic package checks
chkpypkg venv
chkpypkg pip

if (( ${#missing_pypkg[@]} > 0 )); then
  echo "ERROR: Missing packages detected."
  unset missing_pypkg
  return 2
fi
unset missing_pypkg
# End package checks

VENV_CMD="${PYTHON_CMD} -m venv"


if [ -d "${IPBB_VENV}" ] ; then
    echo -e "${COL_YELLOW}WARNING: ${IPBB_VENV} already exists. Delete it before running $(basename $SH_SOURCE).${COL_NULL}"
else
    echo -e "${COL_YELLOW}Virtualenv ${IPBB_VENV} does not exist.${COL_NULL}"
    echo -e "${COL_GREEN}Setting up a new virtual python environment in ${IPBB_VENV}${COL_NULL}"

    IPBB_PIP_INSTALLOPT="-U -I -q"
    IPBB_PIP_INSTALLOPT="-U -I"

    ${VENV_CMD} ${IPBB_VENV}
    source ${IPBB_VENV}/bin/activate

    echo -e "${COL_BLUE}Upgrading python tools...${COL_NULL}"

    # upgrade pip to the latest greatest version
    pip install ${IPBB_PIP_INSTALLOPT} pip 
    pip install ${IPBB_PIP_INSTALLOPT} setuptools virtualenv pur==5.4.1

    echo -e "${COL_BLUE}Installing ipbb...${COL_NULL}"

    PIP_CMD="pip install ${IPBB_PIP_INSTALLOPT} --no-cache-dir --editable file://${IPBB_ROOT}${IPBB_EXTRAS_DEPS+[${IPBB_EXTRAS_DEPS}]}"
    echo -e "Executing '${PIP_CMD}'"
    ${PIP_CMD}

    echo -e "${COL_GREEN}Setup completed${COL_NULL}"
    deactivate
fi