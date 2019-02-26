#------------------------------------------------------------------------------
function pathadd() {
  # Assert that we got enough arguments
  if [[ $# -ne 2 ]]; then
    echo "path add: needs 2 arguments"
    return 1
  fi
  PATH_NAME=$1
  if [[ "$IAM" == "bash" ]]; then
    PATH_VAL=${!1}
  elif [[ "$IAM" == "zsh" ]]; then
    PATH_VAL=${(P)1}
  else
    echo -e "${COL_RED}ERROR: Failed to add ${PATH_ADD} to ${PATH_NAME}${COL_NULL}"
    return
  fi
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

# -----------------------------------------------------------------------------
# Shell identifier
if [ -n "$ZSH_VERSION" ]; then
    # assume Zsh
    IAM="zsh"
    [[ $ZSH_EVAL_CONTEXT =~ :file$ ]] && SH_SOURCED=1 || SH_SOURCED=0
elif [ -n "$BASH_VERSION" ]; then
    # assume Bash
    IAM="bash"
    (return 2>/dev/null) && SH_SOURCED=1 || SH_SOURCED=0
else
    # asume something else
    IAM="unknown"
    SH_SOURCED="unknown"
fi

# -----------------------------------------------------------------------------
# Colors
COL_RED="\e[31m"
COL_GREEN="\e[32m"
COL_YELLOW="\e[33m"
COL_BLUE="\e[34m"
COL_NULL="\e[0m"


#------------------------------------------------------------------------------
# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
HERE=$(cd $(dirname ${SH_SOURCE}) && pwd)

IPBB_VENV=$(cd ${HERE}/.. && pwd)/ipbb
IPBB_ROOT=$(cd ${HERE}/../.. && pwd)

if [[ "${IPBB_VENV}" != "${IPBB_ROOT}/venv/ipbb" ]]; then
  echo -e "${COL_YELLOW}WARNING: Looks like this script was moved from its original location. Stopping here.${COL_NULL}"
  [[ ${SH_SOURCED} -eq 0 ]] && return -1 || exit -1
fi



# -----------------------------------------------------------------------------
# Python version
PYTHON_MAJOR=$(python -c 'from sys import version_info; print (version_info[0])')
PYTHON_MINOR=$(python -c 'from sys import version_info; print (version_info[1])')
PYTHON_VERSION="${PYTHON_MAJOR}.${PYTHON_MINOR}"

