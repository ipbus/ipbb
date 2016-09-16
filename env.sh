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

SH_SOURCE=${BASH_SOURCE}
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)
pathadd PATH ${HERE}

export PATH
