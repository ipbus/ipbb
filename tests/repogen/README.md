# Repository generators

The files in this folder are input files for the `generate-ipbb-repo` tool, each one containing the description (in `yaml`) of an ipbb repo.
The primary purpose for the generated repositories is testing `dep` and `d3` parsing.

* `simple`: Simple repository example;
* `simple_d3`: Same, but in d3 formart;
* `abcd_d3`: Multiple inclusion of the same file (diamond pattern);
* `broken_d3`: Example with Syntax error;
* `hls_simple_d3`: Simple HLS repository;
* `hls_test_d3`: Test HLS repositoy. Generates a minimal working example.