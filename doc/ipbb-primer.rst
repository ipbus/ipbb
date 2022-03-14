.. _ipbb-primer:

IPBB primer
===========

IPBB (IPbus Build tool) is a command-line firmware management and build tool. 

Firmware projects for modern FPGAs typically consist of hundreds of source code files, and make use of components from common packages that have been created by different developers and institutes. IPBB was designed in order to ensure that setting up and building this type of complex firmware project would be simple and reproducible, under all circumstances.

IPBB supports both Vivado and ModelSim/QuestaSim, providing a simple command-line interface for project creation, synthesis, implementation and bitfile generation. The firmware design's HDL code (e.g. VHDL/Verilog files), IP cores and TCL scripts are specified in **dependency** (``.dep``) **files**. The source code for designs is often stored in SVN or git repositories, and these can easily be added to an IPBB working area through the ``ipbb add svn`` and ``ipbb add git`` commands. IPBB also supports automated generation of IPbus address decoder logic from uHAL address tables, as part of the build process (through the ``ipbb vivado gendecoers`` command). 


Downloading IPBB
----------------

IPBB is a standalone package, independent from the firmware area (i.e. you can use the same IPBB installation for many different IPBB work areas and Vivado/Modelsim projects). The latest version of IPBB - 0.5.2 - can be downloaded as follows:

.. code-block:: sh

  cd /path/to/some/directory 
  curl -L https://github.com/ipbus/ipbb/archive/v0.5.2.tar.gz | tar xvz
  # Optionally
  mv ipbb-0.5.2 ipbb


In order to run IPBB commands, you will need to source the environment script from the downloaded ``ipbb`` directory - i.e:

.. code-block:: sh

  source /some-path/ipbb/env.sh

This command sets up the Python evironment (first time after download only), and activates it, making the ``ipbb`` command available regardless of the current working directory. 

The shell prompt is prefixed with ``(ipbb)`` when the ``ipbb`` virtualenv is active. You can de-activate this virtualenv and restore the original shell environment by typing ``deactivate``.


IPBB commands
-------------

IPBB help is available by typing ``ipbb -h``, or ``ipbb <cmd> -h`` or ``ipbb <cmd> <subcmd> -h`` etc. If you're at a terminal, and have momentarily forgotten the name of a command or the correct arguments for a particular command, running ``ipbb -h`` or ``ipbb <cmd> -h`` can often be the quickest way to find out the correct answer.

In bash IPBB supports command completion. When called with no arguments, the ``ipbb`` command enters an interactive shell (auto-completion is available there as well).


.. Vivado workflow: Creating a Vivado project and building a bitfile
.. ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. ADD CONTENT (table of vivado-related commands)


Dependency files
----------------

Dependency files describe the relations between the different elements (e.g. HDL source code, IP cores, constraints, address tables) of the components and projects in a single package, as well as the relationship between different packages. They are parsed by the build tool to generate the list of files that are required to build a bitfile or run simulation.

IPBB requires each firmware project to have a top-level dependency file; IPBB reads this file to determine the full list of files that are required to build a bitfile or run a simulation.


Syntax
^^^^^^

A dependency file simply contains a list of statements - one per line, in the following format::

  command [options] [arguments]

As explained in the following sections, these statements are either used to include the statements from other dependency files, or to directly reference:

* a source code file (e.g. VHDL or Verilog);
* a Vivado IP core config file (``.xci``);
* a TCL script; or
* an address table.

Lines beginning with ``#`` are treated as comments and ignored when IPBB parses dependency files.

.. note:: Dependency files are parsed from the last line of a file to the first line - so for example, if a particular TCL script is referenced at the end of a ``.dep`` file, then that TCL script will be run before all other TCL scripts referenced from that ``.dep`` file.


Common options
^^^^^^^^^^^^^^

``-c component_path``
  Look under a different component to find referenced file. If the component is
  from another package, then the name of that package should be written at the
  start of this path, followed by a colon, e.g. ``other-package:some_component``;
  if there is no colon in the path, then by default the file is assumed to come
  from the same package.


Commands and specific options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``include [<dep_file_path>...]``
  Includes the specified ``.dep`` file(s). If no files are specified, then by default includes 
  ``<basename(component_path)>.dep``. By default, assumes that files are under a ``firmware/cfg``
  subdirectory within the component's base path.

``setup [<tcl_file_path>...]``
  Imports the specified ``.tcl`` script(s) for later processing by the Vivado/ModelSim
  Tcl interface. By default, assumes that files are under a ``firmware/cfg``
  subdirectory within the component's base path.

``src <file_path>...``
  Adds the specified file(s) to the project; glob patterns can be used. By default, assumes that
  files are under a ``firmware/hdl`` subdirectory within the component's base path.
  
``addrtab [-t] <address_file>...``
  Adds the specified address table file(s) to the project. If no files are specified, then adds file 
  ``<component_name>.xml``. By default, assumes that files are under a ``addr_table`` subdirectory
  within the component's base path.

  ``-t``: Marks this file as an address table from which address decoder logic should be generated

