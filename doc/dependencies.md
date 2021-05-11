# Dependency Tree file format (.dep, .d3) reference
## **Work In Progress**

Add here a brief introduction explaining the purpose.
Introduce dep commands, variables and conditional statements.


## Packages and components

Describe here the concept of packages, components and the syntax used to refer to a specific component in a package.
Mention the minimal requirements for a component (`firmware` subdirectory with cfg folder in it (?))

### Component subfolder structure
 * `addr_Table/`
 * `firmware/`
   * `hdl/`
   * `cfg/`
   * `ucf/`

 * `software/`

**Common options**

* `-c`/`--component`: Specifies the package/component in which the file/folder referred by the current command is supposed to be located.
* `--cd`: Change the lookup path for the current command.

## `dep` commands

* `src`: Add a source or constraint file
  - `-l`/`--lib`: Add the hdl file to a library
  - `--vhdl2008`: Use the 2008 vhdl standard for this file
  - `-u`/`--usein` (`synth`,`sim`): Declae the file as synth or sim-only file
  - `--simflags`: Pass flags to Modelsim/Questasim

* `addrtab`: Add an address table file
  - `-t`/`--toplevel`: Top-level address table

* `setup`: Add a project setup file for the current toolset
  - `-f`/`--finalise`: Execute the script after all source files have been included.

* `include`: Include a sub dep-file.

* `util`: Include *utility* files, not directly part of the source gateware but relevant for the project (e.g. a Vivado diagnostic scripts)

* `iprepo`: Adds the path to the list of available ip repositories.

## `dep` vs `d3` files

The two file types supported by `ipbb`, `dep` and `d3` (dep-tree), are identical in content, but differ by the order with witch *dep* commands are parsed.

`dep` files commands are read from bottom to top and, within the same line, file paths from right to left  Such difference is historical. With this approach the top-level VHDL entity appears at the top of the top dep files, reflecting the file order in the tools (ModelSIM and Vivado). The choice of using a reverse parsing order (dependant entries at the top) has proven counter-intuitive, being inverse of the the ordering used in software context.
(Additionally, while commands follow the inverse ordering, variables are processed in forward order :facepalm:)
`d3` files were introduced to circumvent this issue. They are identical to `dep` file for all intent and purposed except for the processing order which is top-bottom, left-right.


## Variables

Describe the use of variables in relation to the script makers and as a way to selectively include sources.

## Conditional statements

Describe the use of conditional statements to (defined by `?`)
