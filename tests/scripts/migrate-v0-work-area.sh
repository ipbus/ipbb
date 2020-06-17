#!/usr/bin/bash


OLD_WORK=$(find . -name .ipbbwork\*)
OLD_PROJ=$(find . -name .ipbbproj\*)
OLD_USER=$(find . -name .ipbbuser\*)

# '.ipbb_work.yml'
# '.ipbb_proj.yml'
# '.ipbb_user.yml'

echo '--- Old work area files ---'
echo -e "${OLD_WORK// /\\n}"
echo
echo '--- Old project area files ---'
echo -e "${OLD_PROJ// /\\n}"
echo
echo '--- Old user config files ---'
echo -e "${OLD_USER// /\\n}"

read -p "Continue (y/n)?" choice
case "$choice" in 
  y|Y ) 
    [[ -z "${OLD_WORK}" ]] && echo " - No work area files to migrate" || rename .ipbbwork .ipbb_work.yml ${OLD_WORK}
    [[ -z "${OLD_PROJ}" ]] && echo " - No project area files to migrate" || rename .ipbbproj .ipbb_proj.yml ${OLD_PROJ}
    [[ -z "${OLD_USER}" ]] && echo " - No user config files to migrate" || rename .ipbbuser .ipbb_user.yml ${OLD_USER}
    ;;
  * ) echo "No files renamed";;
esac