######################################################################################################
# Used to execute Vivado commands on a project without the Vivado GUI.
#
# To use, type "vivado -mode batch -source make_xci.tcl"
#
# After editing the code below to specify which HLS IP core .zip file you wish to convert to 
# a .xci file, ready for inclusion in a Vivado IPBB project.
#
# Also see
#  https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_1/ug835-vivado-tcl-commands.pdf
#  https://www.xilinx.com/support/documentation/sw_manuals/xilinx2017_4/ug894-vivado-tcl-scripting.pdf
######################################################################################################

# Vivado project name.
set projName MakeXCI

puts "=== Creating/replacing project $projName/$projName.xpr ==="
create_project -verbose -force $projName $projName

puts "The time is: [clock format [clock seconds] -format %H:%M:%S]"

# Get top-level directory of Vivado project
set topDir           [get_property DIRECTORY [current_project] ]

# -- Edit these lines to specify your HLS IP core.

# Directory containing HLS IP core (from HLS project area)
set hlsIPDir         ../hls/HLS_KF/solution1/impl/ip
# This is name of top-level function in HLS code.
set ip_repo_name     kalmanUpdateHLS_top
# The output .xci file will be given this name (+ .xci)
set ip_local_name    kalmanUpdateHLS_IP

puts "Input HLS IP .zip file taken from $hlsIPDir. with top-level HLS function name assumed to be $ip_repo_name."

# -- Define FPGA
# Kintex Ultrascale FPGA
set_property PART xcku115-flvb1760-2-e [current_project]
# Virtex Ultrascale-Plus FPGA
#set_property PART xcvu9p-flgb2104-2-e [current_project]

set_property target_language VHDL [current_project]

# Add IP repository
set_property  ip_repo_paths $hlsIPDir [current_project]
update_ip_catalog

# Create specific IP from repository (makes .xci file)
create_ip -name $ip_repo_name -vendor xilinx.com -library hls -version 1.0 -module_name $ip_local_name

# Print all IPs used by project
report_ip_status

puts "Created $topDir/$projName.srcs/[current_fileset]/ip/$ip_local_name/$ip_local_name.xci"

#--------- TOP-LEVEL TCL SCRIPT ----------

exit
