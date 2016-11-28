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
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)
pathadd PATH ${HERE}/bin
# Temporary
pathadd PYTHONPATH "${HERE}"

export PATH PYTHONPATH

# hash virtualenv 2>/dev/null || { echo >&2 "I require foo but it's not installed.  Aborting."; exit 1; }


if [ ! -d "${HERE}/external" ] ; then
  mkdir ${HERE}/external
fi

if [ ! -d "${HERE}/external/ibb" ] ; then

  virtualenv ${HERE}/external/ibb --no-site-packages
  source ${HERE}/external/ibb/bin/activate

  PYTHON_VERSION=$(python -c 'from sys import version_info; print ("%d.%d" % (version_info[0],version_info[1]))')

  if [ "${PYTHON_VERSION}" == "2.7" ] ; then
    pip install ipython
    pip install click
    pip install pexpect
    pip install -U git+https://github.com/alessandrothea/click-shell.git
  elif [ "${PYTHON_VERSION}" == "2.6" ] ; then
    pip install ipython==1.2.1
    pip install click
    pip install pexpect
    pip install -U git+https://github.com/alessandrothea/click-shell.git
  fi

  deactivate
fi

if [ -z ${VIRTUAL_ENV+X} ] ; then
  echo "Activating env"
  source ${HERE}/external/ibb/bin/activate
fi

# Obscure click vodoo to enable bash autocompletion
eval "$(_IPBB_COMPLETE=source ipbb)"