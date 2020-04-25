# modes:
#
# init: creates project, adds hls and test bench files to it, and create solution with FPGA conf and clock
# project_init: creates project, adds hls and test bench files to it
# solution_init: creates solution with FPGA conf and clock
# run_c_sim: builds and runs C simulation
# run_rtl_sim: builds and runs RTL simulation
# synth: synthetise the code
# setup: opens a project and a solution
#

# Defines the mode that will be run in the script
set mode setup
# Sets the project name we will work on
set project_name First_Test
# Sets the solution name we will work on
set solution_name First_Test
# Sets the HLS files we want to synthetise 
set hls_files [list HLS_Test.cpp]
# Sets the test bench files
set tb_files [list TB_Test.cpp]
# Sets the device we want to synthetise for
set part {xc7k160tfbg484-1}
# Sets the clock frequency (if MHz is appended to the number), or period (if only the number is used)
# 10 = 10 ns
# 40MHz = 25 ns -> set clock 40MHz
set clock 10
# Sets the top-level function name that is going to be starting point for synthetisation
set top_function hls_main

# Collection of utility procedures
source CommonProcedures.tcl

switch $mode {
    init {
      initialise_project $project_name $hls_files $tb_files $top_function
      initialise_solution $project_name $solution_name $part $clock
    }
    project_init {
      initialise_project $project_name $hls_files $tb_files $top_function
    }
    solution_init {
      initialise_solution $project_name $solution_name $part $clock
    }
    run_c_sim {
      run_c_simulation $project_name $solution_name
    }
    run_rtl_sim {
      run_rtl_simulation $project_name $solution_name
    }
    synth {
      synthetise $project_name $solution_name
    }
    setup {
      setup_environment $project_name $solution_name
    }
    default {
        puts "Mode $mode is invalid."
    }
}

