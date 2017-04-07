#!/bin/bash
function pathadd() {
  PATH_NAME=$1
  PATH_VAL=${!1}
  # PATH_VAL=${(P)1} # TODO: Zsh cleanup!
  PATH_ADD=$2
  if [[ ":$PATH_VAL:" != *":$PATH_ADD:"* ]]; then
    # Note
    # ${PARAMETER:+WORD}
    #   This form expands to nothing if the parameter is unset or empty. If it
    #   is set, it does not expand to the parameter's value, but to some text
    #   you can specify
    PATH_VAL="$PATH_ADD${PATH_VAL:+":$PATH_VAL"}"
    echo "- $PATH_NAME += $PATH_ADD"

    # use eval to reset the target
    eval "${PATH_NAME}=${PATH_VAL}"
  fi
}


# for Zsh
#
# typeset -U path
# path+=(~/foo)
#
# To add it to the front
# path=(~/foo "$path[@]")

# TODO: Cleanup
# if [ -n "$ZSH_VERSION" ]; then
#    # assume Zsh
#    SH_SOURCE=${(%):-%N} # Alternative? ${(%):-%x}
# elif [ -n "$BASH_VERSION" ]; then
#    # assume Bash
#    SH_SOURCE=${BASH_SOURCE}
# else
#    # asume something else
#    echo "Error: only bash and zsh supported"
# fi

if ! [ -x "$(command -v virtualenv)" ]; then
  echo 'virtualenv is not installed.' >&2
  return 1
fi

SH_SOURCE=${BASH_SOURCE}
IPBB_ROOT=$(cd $(dirname ${SH_SOURCE}) && pwd)

# add bin and test/bin to PATH
pathadd PATH ${IPBB_ROOT}/bin
pathadd PATH ${IPBB_ROOT}/test/bin

# Temporary
pathadd PYTHONPATH "${IPBB_ROOT}"

export PATH PYTHONPATH

if [ ! -d "${IPBB_ROOT}/external" ] ; then
  mkdir ${IPBB_ROOT}/external
fi

if [ ! -d "${IPBB_ROOT}/external/ipbb" ] ; then

  IPBB_PIP_INSTALLOPT="-U -I"

  virtualenv ${IPBB_ROOT}/external/ipbb --system-site-packages
  source ${IPBB_ROOT}/external/ipbb/bin/activate

  # upgrade pip to the latest greatest version
  pip install --upgrade pip

  PYTHON_VERSION=$(python -c 'from sys import version_info; print ("%d.%d" % (version_info[0],version_info[1]))')

  if [ "${PYTHON_VERSION}" == "2.7" ] ; then
    pip install ${IPBB_PIP_INSTALLOPT} ipython
  elif [ "${PYTHON_VERSION}" == "2.6" ] ; then
    pip install ${IPBB_PIP_INSTALLOPT} ipython==1.2.1
  fi

  pip install ${IPBB_PIP_INSTALLOPT} argparse
  pip install ${IPBB_PIP_INSTALLOPT} click
  pip install ${IPBB_PIP_INSTALLOPT} pexpect
  pip install ${IPBB_PIP_INSTALLOPT} sh
  pip install ${IPBB_PIP_INSTALLOPT} texttable

  deactivate
fi

if [ -z ${VIRTUAL_ENV+X} ] ; then
  echo "Activating ipbb environment"
  source ${IPBB_ROOT}/external/ipbb/bin/activate

  # Consistency check
  if [[ ! ${IPBB_ROOT}/external/ipbb -ef ${VIRTUAL_ENV} ]]; then
    deactivate
    echo "ipbb environment loading failed. Was this directory moved?"
    echo "Delete ${IPBB}/external and source env.sh again."
    return
  fi
fi

# Obscure click vodoo to enable bash autocompletion
eval "$(_IPBB_COMPLETE=source ipbb)"