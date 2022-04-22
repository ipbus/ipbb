# Dependency Tree file format (.d3, .dep) reference
## **Work In Progress**

Add here a brief introduction explaining the purpose.
Introduce dep commands, variables and conditional statements.


## Packages and components

Describe here the concept of packages, components and the syntax used to refer to a specific component in a package.
Mention the minimal requirements for a component (`firmware` subdirectory with cfg folder in it (?))

### Component subfolder structure
 * `addr_table/`
 * `firmware/`
   * `hdl/`
   * `cfg/`
   * `cgn/`
   * `ucf/` or `xdc/`

 * `software/`

**Common options**

* `-c`/`--component`: Specifies the package/component in which the file/folder referred by the current command is supposed to be located.
* `--cd`: Change the lookup path for the current command.

## `dep` commands

* `src`: Add a source or constraint file
  - `-l`/`--lib`: Associate the hdl file to a library
  - `--vhdl2008`: Use the 2008 vhdl standard for this file (vhdl only)
  - `-u`/`--usein` (`synth`,`sim`): Declae the file as synth or sim-only file
  - `--simflags`: Pass flags to Modelsim/Questasim

* `addrtab`: Add an address table file
  - `-t`/`--toplevel`: Top-level address table

* `setup`: Add a project setup file for the current toolset
  - `-f`/`--finalise`: Execute the script after all source files have been included.

* `include`: Include a sub dep-file.

* `util`: Include *utility* files, not directly part of the source gateware but relevant for the project (e.g. a Vivado diagnostic scripts)

* `iprepo`: Adds the path to the list of available ip repositories.

## `.d3` vs `.dep` files

The two types of dependency files are supported by `ipbb`, `.d3` (dep-tree) and `.dep` (obsolete) files. They are identical in content, but differ by the direction in which are parsed.

`.dep` files are the historical `ipbb` dependency format. The sequence of commands is read from bottom to top and, within the same line, file paths from right to left. 
In this approach the top-level VHDL entity appears at the top of the top dep files, reflecting the file order in the tools (ModelSIM and Vivado). Time has shown that a reverse parsing order (dependant entries at the top) is counter-intuitive, being opposite of ordering used in most, it not all, software contexts.
(Additionally, while commands follow the inverse ordering, variables are processed in forward order :facepalm:)
`.d3` files were introduced to circumvent this issue. They are identical to `dep` file for all intent and purposed except for the processing order which is top-bottom, left-right.


## Variables

Describe the use of variables in relation to the script makers and as a way to selectively include sources.

### Common

* `top_entity` (`str`): Name of the top entity
* `device_name` (`str`): Device name (FPGA)
* `device_package` (`str`): FPGA package
* `device_speed` (`str`): FPGA speed grade
* `device_generation` (`str`): FPGA generation e.g. Ultrascale/UltrascalePlus
* `board_name` (`str`): Name of the board
* `pkg2lib_map` (`dict( str: str)`):  package to library mapping for hdl files (exprimental)

### Vivado

* `vivado.sim_top_entity` (`str`): Name of simulation top-entity in vivado
* `vivado.binfile_options` (`str`): Bin file generation specific options
* `vivado.mcsfile_options` (`str`): MCS file generation specific options
* `vivado.svf_jtagchain_devices` (): 

### VitisHLS

### Simulation (Questa/Modelsim)

## Conditional statements

Describe the use of conditional statements to (defined by `?`)
