# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [0.3.0] - Pending
### Changed
- `ipcores` and `project` `sim` commands updated to Vivado 2017.4
- Simplified `ipbb vivado project`: IP syntesis runs are not launched automatically anymore.
- Improved `add git` branch/tag resolution.
- Reworked `sim project` to improve speed and reliability.
- Subcommands `project` renamed `make-project`.

### Added
- `--filter` option to `ipbb dep report`
- `--jobs` option to `ipbb vivado` `synth` and `impl` commands.
- Vivado variant autodetection to `ipb-prog vivado`.

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
