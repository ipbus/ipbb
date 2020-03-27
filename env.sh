# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
IPBB_ROOT=$(cd $(dirname ${SH_SOURCE}) && pwd)

source $IPBB_ROOT/venv/scripts/common_ipbb_venv.sh

#--------------------------
opts=$(getopt -o r -- "$@")
[ $? -eq 0 ] || { 
    echo "${SH_SOURCE}: Incorrect options provided"
    return
}

RESET_VENV=false
eval set -- "$opts"
while true; do
    case "$1" in
    -r)
        RESET_VENV=true
        ;;
    --)
        shift
        break
        ;;
    esac
    shift
done
#--------------------------


if [ ${RESET_VENV} = true ]; then
  echo "Resetting VENV"
  $IPBB_ROOT/venv/scripts/reset_ipbb_venv.sh
fi

# Build the virtual environment
if [ ! -d "${IPBB_VENV}" ] ; then
   $IPBB_ROOT/venv/scripts/setup_ipbb_venv.sh
fi

if [ -z ${VIRTUAL_ENV+X} ] ; then
    echo -e "${COL_GREEN}Activating ipbb environment${COL_NULL}"
    source ${IPBB_VENV}/bin/activate
    
    # Locale settings
    # export LANG=C.utf-8
    # export LC_ALL=C.utf-8
    export LANG=C
    export LC_ALL=C

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

alias reset-ipbb-env='reset_ipbb_venv.sh; deactivate'