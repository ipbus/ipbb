# Bash/Zsh independent way of determining the source path
SH_SOURCE=${BASH_SOURCE[0]:-${(%):-%x}}
IPBB_ROOT=$(cd $(dirname ${SH_SOURCE}) && pwd)

source $IPBB_ROOT/venv/scripts/common_ipbb_venv.sh

# Build the virtual environment
if [ ! -d "${IPBB_VENV}" ] ; then
   $IPBB_ROOT/venv/scripts/setup_ipbb_venv.sh
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