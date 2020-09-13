# Repository generators

The files in this folder are input files for the `generate-ipbb-repo` tool, each one containing the description (in `yaml`) of an ipbb repo.
The primary purpose for the generated repositories is testing `dep` and `d3` parsing.
Each file specifies one or more top dependency file.


* `simple`: Simple repository example.  
  Coverage:
  *  Basic `dep` format parsing over multiple files;
  *  `src` and `include` commands;
  *  Assignment (`@x = "value"`) and conditional (`? x == y`) statements;
  *  Comments (`#`).
    
* `simple_d3`: Identical to `simple`, for `d3` format.

* `simple_hls`: Simple example with HLS specific commands.
   Coverage:
   * `hlssrc` commands.

* `abcd_d3`: Nested includes.  
  Coverage:
  * Nested `include` statements.

* `broken`: Example with unresolved files and syntax errors.  
  Coverage:
  * Unresolved file (`top_unres.d3`);
  * Syntax errors (`top_syntax.d3`) misspelt `srca` command.

* `settings`: Advanced example with hierarchical settings.  
  Coverage:
  * Assignment statement with multi-level parameters (`x.y.z = 3`);
  * Corresponding conditional statements.