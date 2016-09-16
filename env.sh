#!/bin/bash
function pathadd() {
  PATH_NAME=$1
  PATH_VAL=${!1}
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

HERE=$(cd $(dirname ${BASH_SOURCE}) && pwd)
pathadd PATH ${HERE}
