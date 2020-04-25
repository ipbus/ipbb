open_project emp-hls-example
set CFLAGS {-std=c++11}
set SRC_PATH {../../src/emp-hls-example/components/firmware/hls}

puts "$SRC_PATH/func.hh"
puts "$SRC_PATH/func.cc"
add_files  -cflags $CFLAGS "$SRC_PATH/func.h"
add_files  -cflags $CFLAGS "$SRC_PATH/func.cc"

set_top myfunc

open_solution solution1

set_part {xcku15p-ffva1760-2-e} -tool vivado

# Encourage HLS to make more effort to find best solution.
# config_bind -effort high
# config_schedule -effort high -relax_ii_for_timing=0 -verbose
# Allow HLS to use longer names in resource/latency usage profiles.
# config_compile -name_max_length 100
# Remove variables from top-level interface if they are never used.
# config_interface -trim_dangling_port
#
# Add HLS directives
#source "vivado_hls_directives.tcl"
#
# Compile & create IP Core
# csim_design -clean -compiler gcc -mflags "-j8"
csynth_design
# Comment out the next 2 lines to speed things up if you are just optimising code.
# cosim_design -trace_level port -rtl vhdl
#cosim_design -trace_level all -rtl vhdl
# Adding "-flow impl" to this causes full Vivado implementation to be run, providing accurate resource use numbers (very slow).
export_design -rtl vhdl -format ip_catalog
#export_design -flow impl -rtl vhdl -format ip_catalog
#
# puts "Synthesis timing & utilization report in HLS_KF/$solution/syn/report/kalmanUpdate_top_csynth.rpt"
# puts "Post-vivado report (more accurate) in ./HLS_KF/solution1/impl/report/vhdl/kalmanUpdate_top_export.rpt"

# puts "Compare output digi tracks from c++ & VHDL in 1st & 2nd half of following printout"
# puts {grep "OUTPUT DIGI STATE" HLS_KF/solution1/sim/report/vhdl/kalmanUpdate_top.log}
# exit
