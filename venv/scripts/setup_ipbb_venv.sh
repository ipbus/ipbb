#!/bin/bash


declare -a missing_pypkg

function chkpypkg() {
  if python -c "import pkgutil; raise SystemExit(1 if pkgutil.find_loader('${1}') is None else 0)" &> /dev/null; then
    echo "${1} is installed"
else
    echo "Error: package '${1}' is not installed"
    missing_pypkg+=(${1})
fi
}
# -----------------------------------------------------------------------------

# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)

# Load common stuff
source ${HERE}/common_ipbb_venv.sh

# Basic package checks
if [[ "${PYTHON_MAJOR}" == "3" ]]; then
    chkpypkg venv
elif [[ "${PYTHON_MAJOR}" == "2" ]]; then
    # chkpypkg virtualenv
    if ! [ -x "$(command -v virtualenv)" ]; then
        missing_pypkg+=('virtualenv')
    fi
fi

chkpypkg pip

if (( ${#missing_pypkg[@]} > 0 )); then
  echo "Aborting."
  unset missing_pypkg
  return 1
fi
unset missing_pypkg
# End package checks


# Virtualenv Setup
VENV2_CMD="virtualenv"
VENV3_CMD="python3 -m venv"

if [[ "${PYTHON_MAJOR}" == "3" ]]; then
    # echo -e "${COL_GREEN}Python 3 detected${COL_NULL}"
    VENV_CMD=${VENV3_CMD}
elif [[ "${PYTHON_MAJOR}" == "2" ]]; then
    # echo -e "${COL_GREEN}Python 2 detected${COL_NULL}"
    VENV_CMD=${VENV2_CMD}
else
    echo -e "${COL_RED}Unupported python version ${PYTHON_MAJOR}${COL_NULL}"
    exit -1
fi


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
    pip install ${IPBB_PIP_INSTALLOPT} setuptools virtualenv pur

    echo -e "${COL_BLUE}Installing ipbb...${COL_NULL}"

    pip install ${IPBB_PIP_INSTALLOPT} --no-cache-dir --editable ${IPBB_ROOT}

    echo -e "${COL_GREEN}Setup completed${COL_NULL}"
    deactivate
fi