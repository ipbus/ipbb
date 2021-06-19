# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
IPBB_ROOT=$(cd $(dirname ${SH_SOURCE}) && pwd)

source $IPBB_ROOT/venv/scripts/common_ipbb_venv.sh

#--------------------------
opts=$(getopt -o 'rd' -l 'reset,develop' -- "$@")
[ $? -eq 0 ] || { 
    echo "${SH_SOURCE}: Incorrect options provided"
    return
}

RESET_VENV=false
IPBB_EXTRAS_DEPS=""
eval set -- "$opts"
while true; do
    case "$1" in
        (-r|--reset)
            RESET_VENV=true
            shift;;
        (-d|--develop)
            IPBB_EXTRAS=develop
            shift;;
        (--)
            shift
            break
            ;;
    esac
done
#--------------------------

# Locale settings
if [[ ! -z "${PYTHON_PATH}" ]]; then
    echo -e "${COL_GREEN}Python 3 detected${COL_NULL}"
else
    echo -e "${COL_RED}Unupported python version ${PYTHON_MAJOR}${COL_NULL}"
    return
fi

export LANG="en_US.utf8"
export LC_ALL="en_US.utf8"


if [ ${RESET_VENV} = true ]; then
  echo "Resetting VENV"
  $IPBB_ROOT/venv/scripts/reset_ipbb_venv.sh
fi

# Build the virtual environment
if [ ! -d "${IPBB_VENV}" ] ; then
   $IPBB_ROOT/venv/scripts/setup_ipbb_venv.sh ${IPBB_EXTRAS_DEPS}
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

# add tests/bin to PATH
pathadd PATH ${IPBB_ROOT}/tests/scripts
pathadd PATH ${IPBB_ROOT}/venv/scripts
pathadd PATH ${IPBB_ROOT}/tools/bin


# Obscure click vodoo to enable bash autocompletion
if [[ "$IAM" == "bash" ]]; then
  # eval "$(_IPBB_COMPLETE=source ipbb)"
  # eval "$(_IPB_PROG_COMPLETE=source ipb-prog)"  
  source ${IPBB_ROOT}/etc/bash_completion/ipbb
  source ${IPBB_ROOT}/etc/bash_completion/ipb-prog
elif [[ "$IAM" == "zsh" ]]; then
  eval "$(_IPBB_COMPLETE=source_zsh ipbb)"
  eval "$(_IPB_PROG_COMPLETE=source_zsh ipb-prog)"  
fi

unset RESET_VENV
unset IPBB_EXTRAS_DEPS

alias reset-ipbb-env='reset_ipbb_venv.sh; deactivate'