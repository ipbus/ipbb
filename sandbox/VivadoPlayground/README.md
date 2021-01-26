# VivadoPlayground
Testing area with useful stuff for VivadoHLS

## Running the test
By running
```bash
vivado_hls -f CommonWorkflows.tcl
```
the vivado project can be created and run.
The main handle to decide which workflow will be run is the variable ```mode``` in the ```CommonWorkflows.tcl``` script.
These modes have been implemented:
 * ```init```: creates project, adds hls and test bench files to it, and creates a solution with FPGA conf and clock
 * ```project_init```: creates project, adds hls and test bench files to it
 * ```solution_init```: creates solution with FPGA conf and clock
 * ```run_c_sim```: builds and runs C simulation
 * ```run_rtl_sim```: builds and runs RTL simulation
 * ```synth```: synthesises the HLS code
 * ```setup```: opens a project and solution to start the interactive session

 
## Some basic concepts and relative examples in the repository

### Project
A **project** is a collection of files and solutions.
A project is created (or opened, if already existing) by running ```open_project <project_name>```.
In this repo the project name is ```First_Test```.

### Solutions
Vivado HLS allows the user to synthesise the same code on a variety of device and with a variety of optimisations. A **solution** enables to target a specific device with a specific frequency and optimisation for the code in the project. By having multiple solutions different optimisation and devices can be targeted while keeping the same code, in order to test which settings works best for the project.
A solution can be added to a project (or opened, if already existing) by running ```open_solution <solution_name>```.
```set_part <part_name>``` and ```create_clock -period <clock>``` enable to set the target FPGA and the clock frequency. Clock frequency can be specified as a number to give the period in ns (e.g. ```create_clock -period 10``` would set it to 10 ns), or as a frequency (e.g. ```create_clock -period 10MHz``` sets it to 10 MHz).

### Files in a HLS project
In HLS you have two type of files: the HLS C files, and the test bench files.

#### HLS C files
These are the actual files that will be synthesised to FPGA FW.
You add those files to an opened project by running ```add_files <file1> <file2> ...```. 
**Please note that including .h files is discouraged.**
HLS requires an explicit declaration of what your top-level function is going to be, you provide it by running ```set_top <function_name>```.
In this repository ```HLS_Test.cpp``` is our test HLS file, and ```hls_main()``` is our top-level function.

#### Test bench files
These are the files used to test your HLS code in simulations. 
The file ```TB_Test.cpp``` is the file that is compiled into the C++ simulation. It contains the ```main()``` and links to the HLS code in ```HLT_Test.cpp``` through the header ```HLT_Test.h```.
Test bench files are added to the project using ```add_files -tb <file1> <file2> ...```.

## Code simulation
You can have 2 different types of simulation: C simulation, and RTL simulation.

### Running C simulation
In the C simulation you basically compile your entire code (test bench + HLS code) under GCC and you run your test on it.
To run the test bench, you run ```csim_design```. The command compiles in gcc/g++ the code and runs it. The ```main``` must be designed in order to return 0 if the test has succeeded.  Any other value is interpreted has not succeeded.
By running ```csim_design -setup```, it is possible to compile without running.

### Running RTL simulation

RTL simulation takes the synthesised code and puts in a emulator that runs it.
**To run the RTL simulation, you must first synthesise the code by running ```csynth_design```.** This command generates the RTL.
Second step is running ```cosim_design```, this command:
 1) Runs the C simulation (i.e. runs ```csim_design```)
 2) If the test is succeeded (i.e. the main returns 0), the C simulation is run again until the top-level function is called. 
 3) At that point the arguments of the top-level function are converted to RTL inputs and the RTL simulation of the top-level function is run.
 4) The output of the RTL simulation is taken, reconverted to C data and the execution of the C code is resumed.
 5) If the main return 0, the test is considered passed, otherwise failed.
 

## Other stuff

### Have specific code blocks running only in C sim
  The compiler defines ```__SYNTHESIS___``` when synthesising stuff.
  Therefore with a ```#ifdef __SYNTHESIS__``` code blocks running only in the C simulation can be added. 
  This can be used to add debug printouts (```std::cout``` would not work on synthesis) and other C-only features.