proc initialise_solution {projectName solutionName part clock} {
  open_project $projectName
  open_solution -reset $solutionName
  set_part $part
  create_clock -period ${clock}
  puts "Run 'build_c_simulation $projectName $solutionName' to build the C simulation."
}

proc initialise_project {projectName hls_files tb_files top_func} {
  open_project -reset $projectName
  
  foreach file $hls_files {
    add_files $file
  }
  
  foreach file $tb_files {
    add_files -tb $file
  }
  
  set_top $top_func
  puts "Run 'initialise_solution solutionName part clock' to create a solution."
}

proc run_c_simulation {projectName solutionName} {
  open_project $projectName
  open_solution $solutionName
  csim_design
}

proc setup_environment {projectName solutionName} {
  open_project $projectName
  open_solution $solutionName
  puts "Opened solution $solutionName in project $projectName."
}

proc synthetise {projectName solutionName} { 
  open_project $projectName
  open_solution $solutionName
  csynth_design
}

proc run_RTL_simulation {projectName solutionName} { 
  open_project $projectName
  open_solution $solutionName
  csynth_design
  cosim_design
}