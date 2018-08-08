#!/bin/bash

COL_RED="\e[31m"
COL_GREEN="\e[32m"
COL_YELLOW="\e[33m"
COL_BLUE="\e[34m"
COL_NULL="\e[0m"


#------------------------------------------------------------------------------
function pathadd() {
  # Assert that we got enough arguments
  if [[ $# -ne 2 ]]; then
    echo "drop_from_path: needs 2 arguments"
    return 1
  fi
  PATH_NAME=$1
  PATH_VAL=${!1}
  PATH_ADD=$2

  # Add the new path only if it is not already there
  if [[ ":$PATH_VAL:" != *":$PATH_ADD:"* ]]; then
    # Note
    # ${PARAMETER:+WORD}
    #   This form expands to nothing if the parameter is unset or empty. If it
    #   is set, it does not expand to the parameter's value, but to some text
    #   you can specify
    PATH_VAL="$PATH_ADD${PATH_VAL:+":$PATH_VAL"}"

    # echo "- $PATH_NAME += $PATH_ADD"
    echo -e "${COL_BLUE}Added ${PATH_ADD} to ${PATH_NAME}${COL_NULL}"

    # use eval to reset the target
    eval "${PATH_NAME}=${PATH_VAL}"
  fi
}
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
PYTHON_MAJOR=$(python -c 'from sys import version_info; print (version_info[0])')
PYTHON_MINOR=$(python -c 'from sys import version_info; print (version_info[1])')
PYTHON_VERSION="${PYTHON_MAJOR}.${PYTHON_MINOR}"

# Check python version
if [ "${PYTHON_MAJOR}" != "2" ]; then
  echo -e "${COL_RED}Python > 2 is not supported (python ${PYTHON_VERSION} detected)${COL_NULL}"
  return 1
fi

# Check if virtualenv is installed
if ! [ -x "$(command -v virtualenv)" ]; then
  echo -e "${COL_RED}virtualenv is not installed. Please install virtualenv and source ${BASH_SOURCE} again.${COL_NULL}" >&2
  return 1
fi

# Check if virtualenv is installed
if ! [ -x "$(command -v pip)" ]; then
  echo -e "${COL_RED}pip is not installed. Please install pip and source ${BASH_SOURCE} again.${COL_NULL}" >&2
  return 1
fi

# SH_SOURCE=${BASH_SOURCE}

if [ -n "$ZSH_VERSION" ]; then
   # assume Zsh
   SH_SOURCE=${(%):-%x}
elif [ -n "$BASH_VERSION" ]; then
   # assume Bash
   SH_SOURCE=${BASH_SOURCE}
else
   # asume something else
   echo "Error: only bash and zsh supported"
fi

IPBB_ROOT=$(cd $(dirname ${SH_SOURCE}) && pwd)
IPBB_VENV=${IPBB_ROOT}/external/ipbb

export IPBB_ROOT PATH PYTHONPATH

if [ ! -d "$(dirname ${IPBB_VENV})" ] ; then
  mkdir -p $(dirname ${IPBB_VENV})
fi

if [ ! -d "${IPBB_VENV}" ] ; then

  echo -e "${COL_YELLOW}Virtualenv ${IPBB_VENV} does not exist.${COL_NULL}"
  echo -e "${COL_GREEN}Setting up a new virtual python environment in ${IPBB_VENV}${COL_NULL}"

  IPBB_PIP_INSTALLOPT="-U -I -q"

  virtualenv ${IPBB_VENV} --system-site-packages
  source ${IPBB_VENV}/bin/activate

  echo -e "${COL_BLUE}Upgrading python tools...${COL_NULL}"

  # upgrade pip to the latest greatest version
  pip install -q --upgrade pip


  if [ "${PYTHON_VERSION}" == "2.7" ] ; then
    pip install ${IPBB_PIP_INSTALLOPT} ipython
  elif [ "${PYTHON_VERSION}" == "2.6" ] ; then
    pip install ${IPBB_PIP_INSTALLOPT} ipython==1.2.1
  fi

  echo -e "${COL_BLUE}Installing ipbb...${COL_NULL}"

  pip install -q --no-cache-dir --editable ${IPBB_ROOT}

  echo -e "${COL_GREEN}Setup completed${COL_NULL}"
  deactivate
fi

if [ -z ${VIRTUAL_ENV+X} ] ; then
  echo -e "${COL_GREEN}Activating ipbb environment${COL_NULL}"
  source ${IPBB_VENV}/bin/activate

  # Consistency check
  if [[ ! ${IPBB_VENV} -ef ${VIRTUAL_ENV} ]]; then
    deactivate
    echo -e "${COL_RED}ERROR: ipbb environment loading failed. Was ipbb directory moved?${COL_NULL}"
    echo -e "${COL_RED}       Delete ${IPBB_VENV} and source env.sh again.${COL_NULL}"
    return
  fi
fi

# add test/bin to PATH
pathadd PATH ${IPBB_ROOT}/test/scripts
pathadd PATH ${IPBB_ROOT}/tools/bin

# Temporary
pathadd PYTHONPATH "${IPBB_ROOT}"

# Obscure click vodoo to enable bash autocompletion
eval "$(_IPBB_COMPLETE=source ipbb)"
eval "$(_IPB_PROG_COMPLETE=source ipb-prog)"

echo -e "${COL_GREEN}ipbb environment successfully loaded${COL_NULL}"

