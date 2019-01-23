# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.3.12] - 2019-01-23
### Fixes
- `pip` version constrained to `<19`.

## [0.3.12] - 2019-01-22
### Fixes
- `vivado impl` error-catching settings modified to carry on Critical Errors, except for timing errors.

## [0.3.11] - 2018-12-19
### Fixes
- Target simulator in `sim ipcores` for QuestaSim. Was `questasim` instead of `questa`.

## [0.3.10] - 2018-12-11
### Fixes
- Bug fixed in Modelsim script generator.

## [0.3.9] - 2018-12-01
### Fixes
- Support for hashing custom ip libraries linked by `iprepo` 

### Removed
- `-m` (map) option removed from `src ` dependency command.

## [0.3.8] - 2018-11-26
### Fixes
- Dep parser incorrectly interpreting the library option.

### Changed
- Reworked `modelsim` and `vivado` autodetection logic.
- Xilinx simulation library path now includes modelsim's version.

### Added
- Project user settings.

## [0.3.7] - 2018-10-25
### Fixed
- `env.sh` hanging when setting up the virtual environment.

## [0.3.6] - 2018-10-08
### Added
- `sim make-project` parameters to set sim ip and mac addresses in the `vsim` wrapper script.

## [0.3.5] - 2018-9-27
### Changed
- Support for `click 7.0` module.

## [0.3.4] - 2018-8-31
### Changed
- `ipb-prog` `vivado program` now capable of extrating bitfiles from tarballs. No need to unpack the tarball anymore.

## [0.3.3] - 2018-8-8
### Changed
- Updated `gen_ipus_addr_decode` to the latest version.

### Added
- Support for ZSH.
- Supoort for HLS ipcores.

## [0.3.2] - 2018-5-25
### Changed
- Improved `srcs status` summary for git tags.
- Modelsim workflow updated. Xilinx simlib generation moved to a dedicated command `setup-simlib`.

### Added
- OOC run monitoring in `vivado synth`
- `ipb-prog vivado` hardware URI option for remote hardware servers.
- New `toolbox` command group.
- `toolbox check-dep` command to validate single `dep` files.
- `vivado check-syntax` command to check vhdl syntax before synthesis.
- Colorization of Vivado messages.

## [0.3.0] - 2018-03-11
### Changed
- `ipcores` and `project` `sim` commands updated to Vivado 2017.4
- Simplified `ipbb vivado project`: IP syntesis runs are not launched automatically anymore.
- Improved `add git` branch/tag resolution.
- Reworked `sim project` to improve speed and reliability.
- Subcommands `project` renamed `make-project`.
- Fixed bug in `srcs status`, preventing groups from being displayed correctly.
- Restored `sim ipcores` compatibility with Vivado 2016 and eralier versions.
- `tests/bin` renamed `tests/scripts`

### Added
- `--filter` option to `ipbb dep report`
- `--jobs` option to `ipbb vivado` `synth` and `impl` commands.
- Vivado variant autodetection to `ipb-prog vivado`.
- `srcs run` command, to simplify running commands in the source area.
- `VivadoConsole` can quite on Vivado's CRITICAL WARNINGS
- `--tag` option to `vivado package` to customise the tarball name.

## [0.2.9] - 2018-01-08
### Changed
- Improved ipbus-decoder code diff.
- Standardized `vivado project`, `sim project` and `sim ipcores` options.

### Added
- Check on branch/tag validity when adding git repositories.
- Suppoer for conda-based environment.
- The `cleanup` subcommand to `sim` and `vivado` command groups.
- The `srcstat` command to provide a compact status report of git and svn packages.

## [0.2.8] - 2017-10-05
### Changed
- Improved command-line help.
- Bugfix in `ipbb create vivado`
 
## [0.2.7] - 2017-09-01
### Added
- New script `ipb-prog`, for programming Xilinx board via jtag and `vivado_lab`.
- Virtualenv setup now based on `setuptools`.

### Changed
- Improved error messages.
- Consolidated `ipbb dep report` sections, now organised in text tables.

## [0.2.6] - 2017-07-17

### Changed
- Improved handling of Vivado library paths in Modelsim.
- Command line help improved. 

## [0.2.5] - 2017-04-23
