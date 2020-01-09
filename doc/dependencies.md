## Dependency Tree file format (.dep, .d3)

Add here a brief introduction explaining the purpose.

## Packages and components

Describe here the concept of packages, components and the syntax used to refer to a specific component in a package.
Mention the minimal requirements for a component (`firmware` subdirectory with cfg folder in it (?))

### Component subfolder structure
 * `addr_Table`
 * `firmware`
   * `hdl`
   * `cfg`
   * `ucf`

 * `software`

**Common options**

* `-c`/`--component`: Specifies the package/component in which the file/folder referred by the current command is supposed to be located.
* `--cd`: Change the lookup path for the current command.

## `dep` commands

* `src`: Add a source or constraint file
  - `-l`/`--lib`: Add the hdl file to a library
  - `--vhdl2008`: Use the 2008 vhdl standard for this file

* `addrtab`: Add an address table file
  - `-t`/`--toplevel`: Top-level address table

* `setup`: Add a project setup file for the current toolset
  - `-f`/`--finalise`: Execute the script after all source files have been included.

* `include`: Include a sub dep-file.

* `util`: Include an *utility* file, a file which is not directly part of the source code but is relevant for the project

* `iprepo`: Adds the path to the list of available ip repositories.

## Variables

Describe the use of variables in relation to the script makers and as a way to selectively include sources.

## Conditional statements

Describe the use of conditional statements to (defined by `?`)
