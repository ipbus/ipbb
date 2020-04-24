# HLS configuration

# Delete project so as to reset it.
delete_project ebSpikeTagger
# Create/open project
open_project ebSpikeTagger

# N.B. This flag is only available in Vivado HLS 2018.2 or later.
set CFLAGS {"-std=c++11"}

set_top findSpikes
add_files ../include/EbSpikeTaggerConfiguration.h -cflags $CFLAGS
add_files ../include/EbSpikeTaggerLd.h            -cflags $CFLAGS
add_files ../src/EbSpikeTaggerLd.cc               -cflags "-std=c++11 -I../include -DNCHANNELS=$::env(NCHANNELS)"
add_files -tb ../src/testEbSpikeTagger.cc         -cflags "-std=c++11 -I../include -DNCHANNELS=$::env(NCHANNELS)"
add_files -tb ../data
#
set solution solution1
delete_solution $solution 
open_solution   $solution

# Kintex Ultrascale FPGA
set_part {xcku115-flva2104-1-i} -tool vivado
# Virtex 7
#set_part {xc7vx690tffg1927-3} -tool vivado
#
create_clock -period 160MHz -name default
#
# Encourage HLS to make more effort to find best solution.
config_bind -effort high
config_schedule -effort high
# Allow HLS to use longer names in resource/latency usage profiles.
config_compile -name_max_length 100
#
# Add HLS directives
source "vivado_hls_directives.tcl"
#

# multi threading
set_param general.maxThreads 8

# Compile & create IP Core
csim_design -clean -compiler gcc
csynth_design
# Comment out the next 2 lines to speed things up if you are just optimising code.
cosim_design -trace_level port -rtl vhdl
export_design -rtl vhdl -format ip_catalog
#
puts "Synthesis timing & utilization report in ebSpikeTagger/$solution/syn/report/findSpikes_csynth.rpt"
exit
